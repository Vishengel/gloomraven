import logging
from pathlib import Path
from threading import Thread

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from gloomraven.data_model.element_state import ElementLevel
from gloomraven.gloomraven_manager import GloomravenManager
from gloomraven.web.config import CONFIG

logger = logging.getLogger(__name__)

STATIC_PATH = Path(__file__).parent / "static"


class Status(BaseModel):
    x_haven_address: str
    connected_to_x_haven: bool
    scenario: str | None
    round: int | None
    active_elements: dict[str, str]  # Element name to level name, e.g. {"FIRE": "HALF"}
    n_controlled_lights: int


def _get_status(manager: GloomravenManager) -> Status:
    game_state = manager.last_game_state
    controller = manager.smartlight_controller
    return Status(
        x_haven_address=f"{manager.gloomhaven_client.server_ip}:{manager.gloomhaven_client.server_port}",
        connected_to_x_haven=manager.connected_to_x_haven,
        scenario=game_state.scenario if game_state else None,
        round=game_state.round if game_state else None,
        active_elements={
            element.name: level.name
            for element, level in (game_state.element_state.items() if game_state else [])
            if level != ElementLevel.INERT
        },
        n_controlled_lights=len(controller.light_ids) if controller else 0,
    )


def create_app(manager: GloomravenManager) -> FastAPI:
    app = FastAPI(title="Gloomraven")

    @app.get("/")
    def get_index() -> FileResponse:
        return FileResponse(STATIC_PATH / "index.html")

    @app.get("/api/status")
    def get_status() -> Status:
        return _get_status(manager)

    return app


def start_web_server(manager: GloomravenManager) -> None:
    """Serve the web UI from a background thread, so the main thread keeps handling Ctrl+C and SIGTERM."""
    # No access log: every open page polls the status every few seconds
    uvicorn_config = uvicorn.Config(create_app(manager), host=CONFIG.web_host, port=CONFIG.web_port, access_log=False)
    server = uvicorn.Server(uvicorn_config)
    Thread(target=server.run, daemon=True, name="web-server").start()
    logger.info("Web UI on port %s", CONFIG.web_port)
