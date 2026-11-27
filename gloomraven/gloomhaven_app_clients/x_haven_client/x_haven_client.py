import logging
import socket

from pydantic import BaseModel, Field

from gloomraven.data_model.game_state import GameState
from gloomraven.gloomhaven_app_clients.x_haven_client.config import CONFIG

logger = logging.getLogger(__name__)


class StateMessage(BaseModel):
    # Envelope X-Haven uses for state updates since app v1.14 (protocol version 1)
    index: int = Field(alias="i")
    description: str = Field(alias="d")
    game_state: str = Field(alias="s")  # The game state as a JSON string


class XHavenClient:
    MESSAGE_START = "S3nD:"
    MESSAGE_END = "[EOM]"
    MESSAGE_END_BYTES = MESSAGE_END.encode()
    # Wake up from a blocking read this often, so Ctrl+C is handled promptly on Windows
    RECEIVE_TIMEOUT: float = 1.0  # Seconds
    CONNECT_TIMEOUT: float = 5.0  # Seconds. Without it, connecting to an unreachable host blocks for minutes

    def __init__(self, server_ip: str, server_port: int):
        self.server_ip = server_ip
        self.server_port = server_port
        # Kept as bytes, so a multi-byte character split over two reads is decoded only once complete
        self._unprocessed_data = b""

    def connect(self) -> socket.socket:
        """Connect to the server. Raises an `OSError` when it can't be reached."""
        s = socket.create_connection((self.server_ip, self.server_port), timeout=self.CONNECT_TIMEOUT)
        s.settimeout(self.RECEIVE_TIMEOUT)
        self._unprocessed_data = b""  # Left over from a previous connection, can't be completed any more
        logger.info("Connected to server at %s:%s.", self.server_ip, self.server_port)
        return s

    def receive_data(self, s: socket.socket) -> GameState | None:
        data = self._unprocessed_data + self._receive_chunk(s)

        while self.MESSAGE_END_BYTES not in data:
            # If the EOM marker is not in the data, we haven't received the full message yet
            data += self._receive_chunk(s)

        # Anything after the last end marker is the start of the next message
        complete_data, _, self._unprocessed_data = data.rpartition(self.MESSAGE_END_BYTES)
        return self.process_server_message(complete_data.decode())

    @staticmethod
    def _receive_chunk(s: socket.socket) -> bytes:
        while True:
            try:
                chunk = s.recv(CONFIG.socket_buffer_size)
            except TimeoutError:
                continue
            if not chunk:
                raise ConnectionError("The X-Haven server closed the connection")
            return chunk

    def process_server_message(self, message: str) -> GameState | None:
        # One read can hold several messages
        contents = [frame.strip().removeprefix(self.MESSAGE_START) for frame in message.split(self.MESSAGE_END)]
        # Other messages, like "ping", are not JSON
        state_messages = [content for content in contents if content.startswith("{")]
        if not state_messages:
            return None

        logger.info("Received game state message from server")
        try:
            return self._process_game_state(state_messages[-1])
        except ValueError as exc:
            logger.error("Could not process game state: %s", exc)
        return None

    def _process_game_state(self, message: str) -> GameState:
        state_message = StateMessage.model_validate_json(message)
        game_state = GameState.model_validate_json(state_message.game_state)
        logger.debug("Full game state: %s", game_state)
        return game_state
