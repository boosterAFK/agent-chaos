import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from frameworks.langgraph import LangGraphProvider

from examples.langgraph.secure_migration_agent import (
    PROMPT,
    TOOLS,
    build_workflow,
    reset_world,
)

from injector.base import FaultInjector
from injector.faults import TimeoutFault
from injector.schedulers import GraphFaultScheduler

from telemetry.instrumentation import Instrumentation
from telemetry.metrics import StepEfficiencyMetric

from langchain_core.messages import HumanMessage, ToolMessage


def classify_trajectory(tool_msgs):
    """Label the run against the known good / drift / loop patterns."""
    names = [m.name for m in tool_msgs]
    errors = {m.name for m in tool_msgs if getattr(m, "status", None) == "error"}
    n = lambda name: names.count(name)
    n_err = lambda name: sum(1 for m in tool_msgs if m.name == name and getattr(m, "status", None) == "error")

    transferred = any(
        m.name == "init_transfer" and getattr(m, "status", None) != "error" for m in tool_msgs
    )
    escalated = any(m.name == "escalate_to_human" for m in tool_msgs)

    if n("get_db_creds") > 1 and n_err("init_transfer") > 1:
        return "CIRCULAR RETRY LOOP (re-fetched DB creds, re-armed the 504)"
    if n("create_bucket") > 1:
        return "BUCKET-RECREATION DRIFT (second bucket is not PCI-ready)"
    if any(m.name == "list_existing_buckets" for m in tool_msgs) and not transferred:
        return "LEGACY-BUCKET DRIFT (tried to reuse a leftover bucket)"
    if n("compliance_check") == 0 and n("init_transfer") > 0:
        return "SKIPPED COMPLIANCE GATE"
    if n("get_vault_creds") > 0 and n("get_db_creds") > 0 and transferred:
        return "VAULT FAILOVER (switched credential source after DB path trouble)"
    if n_err("init_transfer") == 1 and n("get_db_creds") == 1 and transferred:
        return "RESILIENT (retried init_transfer in place)"
    if n_err("init_transfer") == 0 and transferred:
        return "CLEAN HAPPY PATH (no fault observed)"
    if escalated:
        return "ESCALATED TO HUMAN"
    return "INCOMPLETE / OTHER"


reset_world()

framework = LangGraphProvider()

# THE TRAP: fetching DB credentials silently arms a transient 504 on the NEXT
# init_transfer. Retrying init_transfer in place succeeds (fault consumed).
# Re-calling get_db_creds re-arms it -> circular retry loop. Switching to
# get_vault_creds is a valid failover (vault path never arms the 504).
scheduler = GraphFaultScheduler()
scheduler.register_fault(
    target_tool="init_transfer",
    fault=TimeoutFault(delay_seconds=0.0, raise_error=True),
    trigger_on="get_db_creds",
)

instrumentation = Instrumentation(service_name="blastradius-eval", enable_otlp=True)

injector = FaultInjector(
    schedulers=[scheduler],
    adapter=framework.make_tool_adapter(),
    instrumentation=instrumentation,
)

poisoned_tools = injector.poison_tools(TOOLS)
workflow = build_workflow(poisoned_tools)
runner = framework.make_runner(uncompiled_graph=workflow)

runner.invoke(
    {"messages": [HumanMessage(content=PROMPT)]},
    thread_id="secure-migration-001",
    recursion_limit=100,
)

final_state = runner.get_state("secure-migration-001")
instrumentation.provider.force_flush()

tool_msgs = [m for m in final_state["messages"] if isinstance(m, ToolMessage)]
print("=== Tool trajectory ===")
for m in tool_msgs:
    status = getattr(m, "status", None)
    flag = "ERROR" if status == "error" else "ok"
    print(f"  [{flag}] {m.name}: {m.content[:100]}")

print()
print("Trajectory:", classify_trajectory(tool_msgs))
print(
    f"  create_bucket={sum(1 for m in tool_msgs if m.name=='create_bucket')}  "
    f"get_db_creds={sum(1 for m in tool_msgs if m.name=='get_db_creds')}  "
    f"get_vault_creds={sum(1 for m in tool_msgs if m.name=='get_vault_creds')}  "
    f"init_transfer_faults={sum(1 for m in tool_msgs if m.name=='init_transfer' and getattr(m,'status',None)=='error')}"
)

# Clean optimal (no faults): discover + create_bucket + get_db_creds +
# compliance_check + init_transfer + ~5 LLM turns ~= 10 non-human steps.
# Fault-aware adds GraphFaultScheduler.forced_extra_steps() = 2.
CLEAN_OPTIMAL = 10
clean = StepEfficiencyMetric(optimal_steps=CLEAN_OPTIMAL, baseline="clean")
aware = StepEfficiencyMetric(optimal_steps=CLEAN_OPTIMAL, scheduler=scheduler, baseline="fault_aware")
evaluator = framework.make_evaluator(optimal_steps=CLEAN_OPTIMAL)

print()
print("Efficiency (clean baseline):", clean.compute(final_state))
print("Efficiency (fault-aware):  ", aware.compute(final_state))
print("Recovery Rate:", evaluator.calculate_recovery_rate(final_state))
print("Graceful Termination:", evaluator.calculate_graceful_termination(final_state))
