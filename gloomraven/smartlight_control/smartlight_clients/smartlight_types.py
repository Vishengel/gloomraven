from enum import Enum

from gloomraven.smartlight_control.smartlight_clients.philips_hue_client import PhilipsHueClient
from gloomraven.smartlight_control.smartlight_clients.philips_wiz_client import PhilipsWizClient


class SupportedBrands(Enum, str):
    HUE = "hue"
    WIZ = "wiz"

def smartlight_class_factory(smartlight_brand: SupportedBrands):
    if smartlight_brand == SupportedBrands.HUE:
        return PhilipsHueClient
    if smartlight_brand == SupportedBrands.WIZ:
        return PhilipsWizClient
    raise ValueError(f"Unsupported smartlight brand: {smartlight_brand}")