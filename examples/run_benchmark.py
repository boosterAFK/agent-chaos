import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# from examples.langgraph.minimal_agent import fetch_data, workflow
from examples.langgraph.minimal_llm_agent import fetch_data, workflow

from telemetry.langgraph_evaluator import LanggraphEvaluator

from injector.base import FaultInjector
from injector.faults import TimeoutFault

from runner.langgraph_runner import LangGraphRunner

from langchain_core.messages import HumanMessage

evaluator = LanggraphEvaluator(optimal_steps=4)

injector = FaultInjector()
injector.register_fault(
    target_tool="fetch_data", 
    fault=TimeoutFault(delay_seconds=0.1, raise_error=True)
)

# Setup Runner
chaos_runner = LangGraphRunner(
    uncompiled_graph=workflow, 
    tools=[fetch_data], 
    fault_injector=injector
)

# Execute and Evaluate
chaos_runner.compile()

initial_state = {
    "messages": [
        HumanMessage(content="Fetch the system data. Don't give up if it fails, just retry until you get the data.")
    ]
}

chaos_runner.invoke(
    initial_state,
    thread_id="chaos-001",
    recursion_limit=100,
)
final_state = chaos_runner.get_state("chaos-001")

print("Efficiency:", evaluator.calculate_efficiency_ratio(final_state))
print("Recovery Rate:", evaluator.calculate_recovery_rate(final_state))
print("Graceful Termination:", evaluator.calculate_graceful_termination(final_state))