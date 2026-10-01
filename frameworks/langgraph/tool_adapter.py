# injector/adapters/langchain.py
from injector.adapters.base import ToolAdapter

class LangGraphToolAdapter(ToolAdapter):
    def get_name(self, tool):            return tool.name
    def get_callable(self, tool):        return tool.func
    def clone_with_callable(self, tool, fn): 
        if getattr(tool, "func", None) is None:
            raise TypeError(
                f"Cannot poison tool '{tool.name}': only langchain_core.tools.Tool "
                "instances created from a function (e.g. via @tool) are supported."
            )
        return tool.model_copy(update={"func": fn})
