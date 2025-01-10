import argparse

from gloomraven.gloomhaven_app_clients.x_haven_client.x_haven_client import XHavenClient
from gloomraven.gloomraven_manager import GloomravenManager
from gloomraven.smartlight_control.smartlight_clients.philips_hue_client import (
    PhilipsHueClient,
)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gl_ip",
        help="IP address of the Gloomhaven helper server",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--gl_port", help="Port of the Gloomhaven helper server", type=int, default=4567
    )
    parser.add_argument("--sl_ip", help="IP address of the smartlight bridge", type=str)
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    x_haven_client = XHavenClient(args.ip, args.port)
    smartlight_client = PhilipsHueClient(args.sl_ip)
    gloomraven_manager = GloomravenManager(x_haven_client, smartlight_client)
    gloomraven_manager.run()
