from injector.base import Fault

import time
from typing import Any

class TimeoutFault(Fault):
    def __init__(self, delay_seconds: float = 5.0, raise_error: bool = True):
        self.delay_seconds = delay_seconds
        self.raise_error = raise_error

    def apply(self, tool_name: str, original_callable, *args, **kwargs) -> Any:
        time.sleep(self.delay_seconds)
        if self.raise_error:
            raise TimeoutError(f"[504] Timeout in tool '{tool_name}' failed to respond in time.")

        return original_callable(*args, **kwargs)

