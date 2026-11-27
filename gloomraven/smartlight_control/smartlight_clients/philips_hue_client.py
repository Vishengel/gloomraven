import logging
from typing import Any

from phue import Bridge, PhueException

from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    AvailableLight,
    SmartlightClient,
)

logger = logging.getLogger(__name__)

HUE_MAX = 65535  # The bridge's hue range is 0-65535, where 65535 is red again

# The state fields that set the light's colour, for each colour mode the bridge reports
COLOR_MODE_FIELDS = {"hs": ("hue", "sat"), "ct": ("ct",), "xy": ("xy",)}


def _get_hue_params_for_color(color: dict[str, int]) -> dict[str, Any]:
    """Convert a color from the element color map (hue in degrees, 0-360) to the bridge's hue range (0-65535)."""
    params: dict[str, Any] = {"on": True} | color  # A light has to be on to change its color
    if "hue" in color:
        params["hue"] = round(color["hue"] / 360 * HUE_MAX) % (HUE_MAX + 1)
    return params


def _get_state_params_to_restore(state: dict[str, Any]) -> dict[str, Any]:
    if not state.get("on"):
        return {"on": False}
    color_fields = COLOR_MODE_FIELDS.get(state.get("colormode", ""), ())
    return {"on": True} | {field: state[field] for field in ("bri", *color_fields) if field in state}


class PhilipsHueClient(SmartlightClient):
    def __init__(self, bridge_ip: str):
        super().__init__()
        self.bridge_ip = bridge_ip
        self.light_names: list[str] = []
        self.bridge = Bridge(self.bridge_ip)
        self.bridge.connect()

        logger.info(
            "Smartlight client of type %s initialized with bridge ip %s",
            self.__class__.__name__,
            self.bridge_ip,
        )

    def _get_light_states(self, light_ids: list[int]) -> dict[int, dict[str, Any]]:
        try:
            # One request for all lights; the bridge keys them by id as a string
            all_lights = self.bridge.get_light()
        except (PhueException, OSError) as exc:
            logger.warning("Could not read the state of the Hue lights, they won't be restored: %s", exc)
            return {}
        return {light_id: all_lights[str(light_id)]["state"] for light_id in light_ids if str(light_id) in all_lights}

    def _set_light_states(self, light_states: dict[int, dict[str, Any]], transition_speed: int | None = None) -> None:
        for light_id, state in light_states.items():
            try:
                self.bridge.set_light(light_id, _get_state_params_to_restore(state))
            except (PhueException, OSError) as exc:
                logger.error("Failed to restore the state of Hue light %s: %s", light_id, exc)

    def get_all_light_ids(self) -> list[int]:
        """Get the IDs of the configured lights, or of all lights if none are configured."""
        try:
            name_to_light = self.bridge.get_light_objects("name")
        except (PhueException, OSError) as exc:
            logger.error("Failed to get lights from Philips Hue bridge: %s", exc)
            return []

        if not self.light_names:
            return [light.light_id for light in name_to_light.values()]

        if missing_names := set(self.light_names) - set(name_to_light):
            logger.warning("Configured Hue lights not found on the bridge: %s", sorted(missing_names))
        return [name_to_light[name].light_id for name in self.light_names if name in name_to_light]

    def select_lights(self, light_keys: list[str]) -> None:
        self.light_names = light_keys

    def rediscover_lights(self) -> None:
        pass  # The bridge keeps track of its lights, and they're read from it every time

    def list_available_lights(self) -> list[AvailableLight]:
        return [
            AvailableLight(
                key=name,
                description=f"id {light.light_id}",
                selected=not self.light_names or name in self.light_names,
            )
            for name, light in self.bridge.get_light_objects("name").items()
        ]

    def change_color_by_light_ids(
        self, light_ids: list[int], color: dict[str, int], transition_speed: int | None = None
    ) -> None:
        self.bridge.set_light(light_ids, _get_hue_params_for_color(color))

    def change_color_by_light_name(self, light_name: str, color: dict[str, int]) -> None:
        try:
            light = self.bridge.get_light_objects("name")[light_name]
            self.bridge.set_light(light.light_id, _get_hue_params_for_color(color))
        except KeyError as exc:
            logger.error("Light '%s' not found on the Philips Hue bridge", exc)
