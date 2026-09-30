import json

from injector.base import Fault

class MalformedJSONFault(Fault):

    def apply(self, tool_name: str, original_callable, *args, **kwargs):
        valid_response = original_callable(*args, **kwargs)

        if isinstance(valid_response, dict):
            # Convert the valid response to a malformed JSON string
            malformed_json = json.dumps(valid_response).replace("{", "[")
            return malformed_json

        return f"{{{valid_response}"  