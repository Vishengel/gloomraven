import logging
from pathlib import Path
from threading import Thread

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from gloomraven.data_model.element_state import ElementLevel
from gloomraven.gloomraven_manager import GloomravenManager
from gloomraven.smartlight_control.light_selection_store import LightSelectionStore
from gloomraven.smartlight_control.smartlight_clients.smartlight_client import AvailableLight
from gloomraven.smartlight_control.smartlight_clients.smartlight_types import SupportedBrands
from gloomraven.smartlight_control.smartlight_controller import SmartlightController
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


class Lights(BaseModel):
    brand: SupportedBrands
    lights: list[AvailableLight]
    names: dict[str, str]  # See LightSelection.names_by_brand


class LightSelectionRequest(BaseModel):
    # At least one: an empty selection means all lights, which is not what unchecking everything suggests
    light_keys: list[str] = Field(min_length=1)


class NamesRequest(BaseModel):
    names: dict[str, str]


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


def _get_controller(manager: GloomravenManager) -> SmartlightController:
    if manager.smartlight_controller is None:
        raise HTTPException(status_code=409, detail="No smartlights configured. Start gloomraven with --sl_type")
    return manager.smartlight_controller


def create_app(
    manager: GloomravenManager,
    brand: SupportedBrands,
    light_selection_store: LightSelectionStore,
) -> FastAPI:
    app = FastAPI(title="Gloomraven")

    def get_lights() -> Lights:
        return Lights(
            brand=brand,
            lights=_get_controller(manager).smartlight_client.list_available_lights(),
            names=light_selection_store.load_names(brand),
        )

    @app.get("/")
    def get_index() -> FileResponse:
        return FileResponse(STATIC_PATH / "index.html")

    @app.get("/api/status")
    def get_status() -> Status:
        return _get_status(manager)

    @app.get("/api/lights")
    def get_available_lights() -> Lights:
        return get_lights()

    @app.put("/api/lights")
    def select_lights(request: LightSelectionRequest) -> Lights:
        controller = _get_controller(manager)
        available_keys = {light.key for light in controller.smartlight_client.list_available_lights()}
        if unknown_keys := set(request.light_keys) - available_keys:
            raise HTTPException(status_code=422, detail=f"Unknown lights: {sorted(unknown_keys)}")
        light_selection_store.save(brand, request.light_keys)
        controller.select_lights(request.light_keys)
        return get_lights()

    @app.put("/api/lights/names")
    def save_names(request: NamesRequest) -> Lights:
        light_selection_store.save_names(brand, request.names)
        return get_lights()

    @app.post("/api/lights/rediscover")
    def rediscover_lights() -> Lights:
        _get_controller(manager).rediscover_lights()
        return get_lights()

    return app


def start_web_server(
    manager: GloomravenManager,
    brand: SupportedBrands,
    light_selection_store: LightSelectionStore,
) -> None:
    """Serve the web UI from a background thread, so the main thread keeps handling Ctrl+C and SIGTERM."""
    # No access log: every open page polls the status every few seconds
    uvicorn_config = uvicorn.Config(
        create_app(manager, brand, light_selection_store),
        host=CONFIG.web_host,
        port=CONFIG.web_port,
        access_log=False,
    )
    server = uvicorn.Server(uvicorn_config)
    Thread(target=server.run, daemon=True, name="web-server").start()
    logger.info("Web UI on port %s", CONFIG.web_port)
