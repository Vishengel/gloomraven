from abc import ABC, abstractmethod
from typing import Dict


class SmartlightController(ABC):
    def __init__(self, bridge_ip: str, bridge_port: int):
        self.bridge_ip = bridge_ip
        self.bridge_port = bridge_port

    @abstractmethod
    def change_color(self, color: Dict[str, int]) -> None:
        raise NotImplementedError
