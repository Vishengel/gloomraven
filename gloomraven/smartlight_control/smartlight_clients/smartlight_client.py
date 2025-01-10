from abc import ABC, abstractmethod
from typing import Dict


class SmartlightClient(ABC):
    def __init__(self, bridge_ip: str):
        self.bridge_ip = bridge_ip

    @abstractmethod
    def change_color(self, color: Dict[str, int], light_name: str) -> None:
        raise NotImplementedError
