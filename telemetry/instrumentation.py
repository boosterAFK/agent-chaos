import time
import uuid
from typing import Any, Dict


class Instrumentation:
    def __init__(self) -> None:
        self.temp_events: Dict[str, Dict[str, Any]] = {}

    def start_event(self, event_name: str, **kwargs) -> str:
        event = {"event_name": event_name, "start_time": self._current_time(), **kwargs}
        event_id = uuid.uuid4().hex
        self.temp_events[event_id] = event
        return event_id

    def close_event(self, event_id: str, **kwargs) -> None:
        if event_id in self.temp_events:
            event = self.temp_events[event_id]
            event["end_time"] = self._current_time()
            event.update(kwargs)
            print(f"Event closed: {event}")
            del self.temp_events[event_id]

    def _current_time(self) -> float:
        return time.time()
