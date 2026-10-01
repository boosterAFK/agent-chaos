from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AgentRunner(ABC):
    def __init__(self) -> None:
        self._is_compiled = False
        self.app: Optional[Any] = None

    def compile(self) -> Any:
        app = self._compile()
        self.app = app
        self._is_compiled = True
        return app

    def invoke(
        self,
        input_data: Dict[str, Any],
        thread_id: str,
        recursion_limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not self._is_compiled:
            self.compile()
        return self._invoke(input_data, self._get_config(thread_id, recursion_limit))

    def get_state(self, thread_id: str) -> Dict[str, Any]:
        self._ensure_compiled()
        return self._get_state(self._get_config(thread_id))

    def update_state(self, thread_id: str, new_state: Dict[str, Any], as_node: Optional[str] = None) -> None:
        self._ensure_compiled()
        self._update_state(self._get_config(thread_id), new_state, as_node)

    def _ensure_compiled(self) -> None:
        if not self._is_compiled:
            raise RuntimeError("The agent graph must be compiled before accessing or mutating state.")

    @abstractmethod
    def _get_config(self, thread_id: str, recursion_limit: Optional[int] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _compile(self) -> Any:
        pass

    @abstractmethod
    def _invoke(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _get_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _update_state(self, config: Dict[str, Any], new_state: Dict[str, Any], as_node: Optional[str] = None) -> None:
        pass
