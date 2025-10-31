from gloomraven.config import BaseConfig
from gloomraven.data_model.element_state import Element

ELEMENT_COLOR_MAP = {
    Element.FIRE: {"hue": 0, "sat": 254, "bri": 254},  # Red
    Element.ICE: {"hue": 258, "sat": 254, "bri": 254},  # Blue
    Element.EARTH: {"hue": 140, "sat": 254, "bri": 254},  # Green
    Element.AIR: {"hue": 220, "sat": 254, "bri": 254},  # Light blue
    Element.LIGHT: {"hue": 70, "sat": 200, "bri": 254},  # Warm yellowish-white
    Element.DARK: {"hue": 275, "sat": 254, "bri": 100},  # Deep purple
}


class Config(BaseConfig):
    @property
    def element_color_map(self) -> dict[Element, dict[str, int]]:
        return ELEMENT_COLOR_MAP

    @property
    def light_transition_interval(self) -> int:
        return 30

    @property
    def light_transition_speed(self) -> int:
        # Currently only implemented for Philips WiZ. Value is a percentage between 20 and 200
        return 20


CONFIG = Config()
