
from abc import ABC, abstractmethod
from typing import Any, Dict


class Metric(ABC):
    name: str

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def compute(self, trajectory: Dict[str, Any]) -> float:
        pass