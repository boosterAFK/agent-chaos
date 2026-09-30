from ..fault_injector import Fault

class RateLimitFault(Fault):
    def __init__(self, max_calls: int = 5):
        self.max_calls = max_calls
        self.call_count = 0

    def apply(self, tool_name: str, original_callable, *args, **kwargs):
        if self.call_count >= self.max_calls:
            raise Exception(f"[429] Simulated rate limit exceeded for tool '{tool_name}'.")
        self.call_count += 1
        return original_callable(*args, **kwargs)