import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from frameworks.langgraph import LangGraphProvider

from examples.langgraph.minimal_llm_agent import PROMPT, TOOLS, build_workflow

from injector.base import FaultInjector
from injector.faults import TimeoutFault
from injector.schedulers import FixedCallScheduler

from telemetry.instrumentation import Instrumentation

from langchain_core.messages import HumanMessage


framework = LangGraphProvider()

scheduler = FixedCallScheduler()
scheduler.register_fault(
    "fetch_data",
    TimeoutFault(delay_seconds=0.1, raise_error=True),
    at_calls=(1, 2),  # the first two calls fail; the third one succeeds
)

instrumentation = Instrumentation(service_name="blastradius-eval", enable_otlp=True)

injector = FaultInjector(schedulers=[scheduler], adapter=framework.make_tool_adapter(), instrumentation=instrumentation)
evaluator = framework.make_evaluator(optimal_steps=4)

poisoned_tools = injector.poison_tools(TOOLS)
workflow = build_workflow(poisoned_tools)

runner    = framework.make_runner(uncompiled_graph=workflow)

initial_state = {
    "messages": [
        HumanMessage(content=PROMPT)
    ]
}

runner.invoke(
    initial_state,
    thread_id="chaos-001",
    recursion_limit=100,
)

final_state = runner.get_state("chaos-001")
instrumentation.provider.force_flush()

print("Efficiency:", evaluator.calculate_efficiency_ratio(final_state))
print("Recovery Rate:", evaluator.calculate_recovery_rate(final_state))
print("Graceful Termination:", evaluator.calculate_graceful_termination(final_state))
