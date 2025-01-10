from abc import ABC, abstractmethod
from typing import Dict, List


class SmartlightClient(ABC):
    def __init__(self, bridge_ip: str):
        # This is under the assumption that other smartlight bridges work similar to Philips Hue. Might change later.
        self.bridge_ip = bridge_ip

    @abstractmethod
    def change_color_by_light_name(
        self, light_name: str, color: Dict[str, int]
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def change_color_by_light_ids(
        self, light_ids: List[int], color: Dict[str, int]
    ) -> None:
        raise NotImplementedError
