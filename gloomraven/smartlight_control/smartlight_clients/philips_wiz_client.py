import asyncio
import colorsys
import logging
from typing import Dict, List

from pywizlight import wizlight

from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    SmartlightClient,
)

logger = logging.getLogger(__name__)


class PhilipsWizClient(SmartlightClient):
    def __init__(self, bridge_ip: str):
        super().__init__(bridge_ip)
        self.bridge_ip = bridge_ip
        self.lights = {}  # Store discovered lights by name or ID

    async def _discover_lights(self):
        """Discover WiZ lights on the network."""
        # For WiZ, you typically need to know the IP addresses of individual bulbs
        # This is a placeholder - you might need to implement light discovery
        # or maintain a list of known light IPs
        pass

    def _run_async(self, coro):
        """Helper to run async functions in sync context."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)

    def change_color_by_light_name(
            self, light_name: str, color: Dict[str, int]
    ) -> None:
        # For WiZ, you'll need to maintain a mapping of names to IP addresses
        # This is a simplified implementation
        light_ip = self.lights.get(light_name)
        if not light_ip:
            logger.error("Light '%s' not found in WiZ lights", light_name)
            return

        self._run_async(self._change_color_async(light_ip, color))

    def change_color_by_light_ids(
            self, light_ips: List[str], color: Dict[str, int]
    ) -> None:
        """Change color for multiple WiZ lights by their IP addresses."""
        tasks = [self._change_color_async(ip, color) for ip in light_ips]
        self._run_async(asyncio.gather(*tasks))

    async def _change_color_async(self, light_ip: str, color: Dict[str, int]):
        """Async method to change light color."""
        try:
            light = wizlight(light_ip)

            # Convert Hue HSV format to WiZ format
            if 'hue' in color and 'sat' in color and 'bri' in color:
                # WiZ uses RGB values, convert from HSV
                h = color['hue'] / 65535.0  # Hue bridge uses 0-65535
                s = color['sat'] / 254.0  # Saturation 0-254
                v = color['bri'] / 254.0  # Brightness 0-254

                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                rgb = (int(r * 255), int(g * 255), int(b * 255))

                await light.turn_on()
                await light.set_rgb(rgb[0], rgb[1], rgb[2])
                await light.set_brightness(int(color['bri']))
            else:
                # Direct RGB values if provided
                if 'r' in color and 'g' in color and 'b' in color:
                    await light.turn_on()
                    await light.set_rgb(color['r'], color['g'], color['b'])
                    if 'bri' in color:
                        await light.set_brightness(color['bri'])

        except Exception as exc:
            logger.error("Failed to change color for WiZ light at %s: %s", light_ip, exc)

    def add_light(self, name: str, ip: str):
        """Add a WiZ light to the known lights dictionary."""
        self.lights[name] = ip
        logger.info("Added WiZ light '%s' at IP %s", name, ip)

    async def turn_on_light(self, light_ip: str):
        """Turn on a WiZ light."""
        try:
            light = wizlight(light_ip)
            await light.turn_on()
        except Exception as exc:
            logger.error("Failed to turn on WiZ light at %s: %s", light_ip, exc)

    async def turn_off_light(self, light_ip: str):
        """Turn off a WiZ light."""
        try:
            light = wizlight(light_ip)
            await light.turn_off()
        except Exception as exc:
            logger.error("Failed to turn off WiZ light at %s: %s", light_ip, exc)