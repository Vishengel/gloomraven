from typing import Dict

from gloomraven.config import BaseConfig
from gloomraven.data_model.element_state import Element

# Hardcoded for now, will be made configurable later
ELEMENT_COLOR_MAP = {
    Element.FIRE: {"hue": 0, "sat": 254, "bri": 244},  # Red
    Element.ICE: {"hue": 46920, "sat": 254, "bri": 254},  # Blue
    Element.EARTH: {"hue": 25500, "sat": 254, "bri": 254},  # Green
    Element.AIR: {"hue": 40000, "sat": 254, "bri": 254},  # Light blue
    Element.LIGHT: {"hue": 12750, "sat": 200, "bri": 254},  # Warm yellowish-white
    Element.DARK: {"hue": 50000, "sat": 254, "bri": 100},  # Deep purple
}


class Config(BaseConfig):
    @property
    def element_color_map(self) -> Dict[Element, Dict[str, int]]:
        return ELEMENT_COLOR_MAP

    @property
    def light_transition_interval(self) -> int:
        return 5


CONFIG = Config()
