import argparse
from enum import Enum

from gloomraven.gloomhaven_app_clients.x_haven_client.x_haven_client import XHavenClient
from gloomraven.gloomraven_manager import GloomravenManager
from gloomraven.smartlight_control.smartlight_clients.philips_hue_client import (
    PhilipsHueClient,
)
from gloomraven.smartlight_control.smartlight_clients.philips_wiz_client import PhilipsWizClient
from gloomraven.smartlight_control.smartlight_clients.smartlight_types import SupportedBrands

from gloomraven.smartlight_control.smartlight_clients.smartlight_types import smartlight_class_factory


class SupportedBrands(str, Enum):
    HUE = "hue"
    WIZ = "wiz"


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
    parser.add_argument("--sl_type", help="Type of smartlight", type=SupportedBrands, choices=list(SupportedBrands))
    sl_ip_required = (parser.parse_known_args()[0].sl_type == SupportedBrands.HUE)
    parser.add_argument("--sl_ip", help="IP address of the smartlight bridge", type=str,
                        required=sl_ip_required)
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    x_haven_client = XHavenClient(args.gl_ip, args.gl_port)
    smartlight_client_class = smartlight_class_factory(args.sl_type)
    smartlight_client = smartlight_client_class(args.sl_ip)
    gloomraven_manager = GloomravenManager(x_haven_client, smartlight_client)
    gloomraven_manager.run()
