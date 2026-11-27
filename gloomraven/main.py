import argparse
import logging
import signal
import sys

from gloomraven.gloomhaven_app_clients.x_haven_client.x_haven_client import XHavenClient
from gloomraven.gloomraven_manager import GloomravenManager
from gloomraven.settings import SettingsStore
from gloomraven.smartlight_control.light_selection_store import LightSelectionStore
from gloomraven.smartlight_control.smartlight_clients.smartlight_types import (
    SupportedBrands,
    smartlight_class_factory,
)
from gloomraven.web.web_app import start_web_server


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--list_lights",
        help="Print the lights found for --sl_type, to fill in LIGHTS in .env, and exit",
        action="store_true",
    )
    parser.add_argument(
        "--sl_type",
        help="Type of smartlight",
        type=SupportedBrands,
        choices=[brand.value for brand in SupportedBrands],
    )
    known_args = parser.parse_known_args()[0]
    parser.add_argument(
        "--gl_ip",
        help="IP address of the Gloomhaven helper server",
        type=str,
        required=not known_args.list_lights,
    )
    parser.add_argument("--gl_port", help="Port of the Gloomhaven helper server", type=int, default=4567)
    sl_ip_required = known_args.sl_type == SupportedBrands.HUE
    parser.add_argument(
        "--sl_ip",
        help="IP address of the smartlight bridge",
        type=str,
        required=sl_ip_required,
    )
    return parser.parse_args()


def _exit_on_sigterm(signum: int, _) -> None:
    # Unwind normally on SIGTERM (e.g. docker stop or systemd), so the lights are restored
    sys.exit(128 + signum)


if __name__ == "__main__":
    args = get_args()
    smartlight_client_class = smartlight_class_factory(args.sl_type)
    smartlight_client = smartlight_client_class(args.sl_ip) if args.sl_ip else smartlight_client_class()
    if args.list_lights:
        print("\n".join(f"{light.key} ({light.description})" for light in smartlight_client.list_available_lights()))
        sys.exit()
    light_selection_store = LightSelectionStore()
    smartlight_client.select_lights(light_selection_store.load(args.sl_type))

    x_haven_client = XHavenClient(args.gl_ip, args.gl_port)
    gloomraven_manager = GloomravenManager(x_haven_client, smartlight_client)
    settings_store = SettingsStore()
    if gloomraven_manager.smartlight_controller:
        gloomraven_manager.smartlight_controller.apply_settings(settings_store.load())
    start_web_server(gloomraven_manager, args.sl_type, light_selection_store, settings_store)
    signal.signal(signal.SIGTERM, _exit_on_sigterm)
    try:
        gloomraven_manager.run()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Stopped by Ctrl+C")
