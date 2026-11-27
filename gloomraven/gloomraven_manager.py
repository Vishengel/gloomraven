import logging
import sys
from contextlib import nullcontext

from gloomraven.config import BASECONFIG
from gloomraven.data_model.game_state import GameState
from gloomraven.gloomhaven_app_clients.x_haven_client.x_haven_client import XHavenClient
from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    SmartlightClient,
)
from gloomraven.smartlight_control.smartlight_controller import SmartlightController

logging.basicConfig(stream=sys.stdout, level=BASECONFIG.log_level)
logger = logging.getLogger(__name__)


class GloomravenManager:
    def __init__(
        self,
        gloomhaven_client: XHavenClient,
        smartlight_client: SmartlightClient | None,
    ):
        self.gloomhaven_client = gloomhaven_client
        self.smartlight_controller = SmartlightController(smartlight_client) if smartlight_client else None

    def run(self) -> None:
        """Process game states until interrupted. The lights are restored however this exits."""
        with (
            self.smartlight_controller or nullcontext(),
            self.gloomhaven_client.connect() as connection,
        ):
            while True:
                if game_state := self.gloomhaven_client.receive_data(connection):
                    self.update(game_state)

    def update(self, game_state: GameState):
        if self.smartlight_controller:
            self.smartlight_controller.update(game_state)
