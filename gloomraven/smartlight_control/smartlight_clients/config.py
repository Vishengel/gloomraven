from pathlib import Path

from pydantic import Field

from gloomraven.config import PROJECT_ROOT_PATH, BaseConfig
from gloomraven.data_model.element_state import Element

ELEMENT_COLOR_MAP = {
    Element.FIRE: {"hue": 0, "sat": 254, "bri": 254},  # Red
    Element.ICE: {"hue": 258, "sat": 254, "bri": 254},  # Blue
    Element.EARTH: {"hue": 120, "sat": 254, "bri": 254},  # Green
    Element.AIR: {"hue": 220, "sat": 254, "bri": 254},  # Light blue
    Element.LIGHT: {"hue": 70, "sat": 200, "bri": 254},  # Warm yellowish-white
    Element.DARK: {"hue": 275, "sat": 254, "bri": 100},  # Deep purple
}


class Config(BaseConfig):
    # Lights to control: MAC addresses for WiZ, light names for Hue. Empty means all lights.
    # Only used until a light selection is saved to light_selection_path
    lights: list[str] = Field(default_factory=list)
    light_selection_path: Path = PROJECT_ROOT_PATH / "resources" / "light_selection.json"
    # Windows can send 255.255.255.255 out of the wrong network adapter (e.g. a Hyper-V switch).
    # Set this to your LAN's broadcast address, e.g. 192.168.178.255, if WiZ discovery finds no lights
    wiz_broadcast_address: str = "255.255.255.255"

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
