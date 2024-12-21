from typing import Dict

from pydantic_settings import BaseSettings

from gloomraven.data_model.element_state import Element

# Hardcoded from now, will be made configurable later
ELEMENT_COLOR_MAP = {
    Element.FIRE: {"hue": 0, "sat": 254, "bri": 254},  # Red
    Element.ICE: {"hue": 46920, "sat": 254, "bri": 254},  # Blue
    Element.EARTH: {"hue": 25500, "sat": 254, "bri": 254},  # Green
    Element.AIR: {"hue": 40000, "sat": 254, "bri": 254},  # Light blue
    Element.LIGHT: {"hue": 40000, "sat": 254, "bri": 254},  # Placeholder
    Element.DARK: {"hue": 40000, "sat": 254, "bri": 254},  # Placeholder
}


class Config(BaseSettings):
    @property
    def element_color_map(self) -> Dict[Element, Dict[str, int]]:
        return ELEMENT_COLOR_MAP


CONFIG = Config()