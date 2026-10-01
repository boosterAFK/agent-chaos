from frameworks.base import FrameworkProvider
from frameworks.langgraph.runner import LangGraphRunner
from injector.adapters.base import ToolAdapter
from frameworks.langgraph.tool_adapter import LangGraphToolAdapter
from frameworks.langgraph.evaluator import LangGraphEvaluator

class LangGraphProvider(FrameworkProvider):

    def make_tool_adapter(self) -> "ToolAdapter":
        return LangGraphToolAdapter()

    def make_runner(self, uncompiled_graph, checkpointer=None) -> "LangGraphRunner":
        return LangGraphRunner(uncompiled_graph, checkpointer=checkpointer)

    def make_evaluator(self, optimal_steps: int) -> "LangGraphEvaluator":
        return LangGraphEvaluator(optimal_steps)