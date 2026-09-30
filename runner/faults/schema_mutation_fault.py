from typing import Any

from ..fault_injector import Fault

class MalformedJSONFault(Fault):
    def __init__(self, missing_key: str):
        self.missing_key = missing_key

    def apply(self, tool_name: str, original_callable, *args, **kwargs) -> Any:
        valid_response = original_callable(*args, **kwargs)

        if isinstance(valid_response, dict):
            # Remove the specified key to simulate a malformed JSON response
            if self.missing_key in valid_response:
                del valid_response[self.missing_key]
            return valid_response

        return f"{{{valid_response}"