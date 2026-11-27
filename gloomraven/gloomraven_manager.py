import logging
import socket
import sys
import time
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
    # Back off while the X-Haven server is down, which can be for months between campaigns
    MIN_RECONNECT_DELAY: float = 1.0  # Seconds
    MAX_RECONNECT_DELAY: float = 60.0  # Seconds

    def __init__(
        self,
        gloomhaven_client: XHavenClient,
        smartlight_client: SmartlightClient | None,
    ):
        self.gloomhaven_client = gloomhaven_client
        self.smartlight_controller = SmartlightController(smartlight_client) if smartlight_client else None
        # Read by the web UI from another thread; each is replaced as a whole, never changed in place
        self.connected_to_x_haven = False
        self.last_game_state: GameState | None = None

    def run(self) -> None:
        """
        Process game states until interrupted, reconnecting whenever the X-Haven server can't be reached.

        The lights are restored however this exits.
        """
        with self.smartlight_controller or nullcontext():
            reconnect_delay = self.MIN_RECONNECT_DELAY
            while True:
                try:
                    connection = self.gloomhaven_client.connect()
                except OSError as exc:
                    logger.warning(
                        "Could not connect to the X-Haven server at %s:%s: %s. Retrying in %s seconds",
                        self.gloomhaven_client.server_ip,
                        self.gloomhaven_client.server_port,
                        exc,
                        reconnect_delay,
                    )
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, self.MAX_RECONNECT_DELAY)
                    continue

                reconnect_delay = self.MIN_RECONNECT_DELAY
                self.connected_to_x_haven = True
                try:
                    self._process_game_states(connection)
                except OSError as exc:
                    logger.warning("Lost the connection to the X-Haven server: %s", exc)
                finally:
                    self.connected_to_x_haven = False

    def _process_game_states(self, connection: socket.socket) -> None:
        with connection:
            while True:
                if game_state := self.gloomhaven_client.receive_data(connection):
                    self.update(game_state)

    def update(self, game_state: GameState):
        self.last_game_state = game_state
        if self.smartlight_controller:
            self.smartlight_controller.update(game_state)
