from pydantic_settings import BaseSettings


class _Config(BaseSettings):
    ELEMENT_COLOR_MAP = {
        "Fire": {"hue": 0, "sat": 254, "bri": 254},  # Red
        "Ice": {"hue": 46920, "sat": 254, "bri": 254},  # Blue
        "Earth": {"hue": 25500, "sat": 254, "bri": 254},  # Green
        "Air": {"hue": 40000, "sat": 254, "bri": 254},  # Light blue
        "Light": {},
        "Dark": {},
    }


CONFIG = _Config
