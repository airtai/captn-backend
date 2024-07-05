import contextlib
import socket
import threading
import time
from platform import system
from typing import Annotated, Any, Callable, Dict, Iterator, List, Optional, Union

import pytest
import uvicorn
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field

from captn.captn_agents.backend.config import Config


@pytest.fixture()
def llm_config() -> Dict[str, List[Dict[str, str]]]:
    return {
        "config_list": Config().config_list_gpt_3_5,
    }


def create_weather_fastapi_app(host: str, port: int) -> FastAPI:
    app = FastAPI(
        title="Weather",
        servers=[
            {"url": f"http://{host}:{port}", "description": "Local development server"}
        ],
    )

    @app.get("/forecast/{city}", description="Get the weather forecast for a city")
    def forecast(
        city: Annotated[str, Path(description="name of the city")],
    ) -> str:
        return f"Weather in {city} is sunny"

    return app


def create_google_sheet_fastapi_app(host: str, port: int) -> FastAPI:
    app = FastAPI(
        title="Google Sheet",
        servers=[
            {"url": f"http://{host}:{port}", "description": "Local development server"}
        ],
    )

    @app.get("/login", description="Get the URL to log in with Google")
    def get_login_url(
        user_id: Annotated[
            int, Query(description="The user ID for which the data is requested")
        ],
        force_new_login: Annotated[bool, Query(description="Force new login")] = False,
    ) -> Dict[str, str]:
        return {
            "url": f"https://accounts.google.com/o/oauth2/auth?user={user_id}&force_new_login={force_new_login}"
        }

    class GoogleSheetValues(BaseModel):
        values: List[List[Any]] = Field(
            ..., title="Values", description="Values to be written to the Google Sheet."
        )

    @app.get("/get-sheet", description="Get data from a Google Sheet")
    def get_sheet(
        user_id: Annotated[
            int, Query(description="The user ID for which the data is requested")
        ],
        spreadsheet_id: Annotated[
            Optional[str],
            Query(description="ID of the Google Sheet to fetch data from"),
        ] = None,
        title: Annotated[
            Optional[str],
            Query(description="The title of the sheet to fetch data from"),
        ] = None,
    ) -> Union[str, GoogleSheetValues]:
        assert user_id != -1
        return GoogleSheetValues(
            values=[
                ["Country", "Station From", "Station To"],
                ["USA", "New York", "Los Angeles"],
            ]
        )

    return app


class Server(uvicorn.Server):  # type: ignore [misc]
    def install_signal_handlers(self) -> None:
        pass

    @contextlib.contextmanager
    def run_in_thread(self) -> Iterator[None]:
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]  # type: ignore [no-any-return]


def _create_fastapi_openapi_url(
    create_app_f: Callable[[str, int], FastAPI],
) -> Iterator[str]:
    host = "127.0.0.1"
    port = find_free_port()
    app = create_app_f(host, port)
    openapi_url = f"http://{host}:{port}/openapi.json"

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = Server(config=config)
    with server.run_in_thread():
        time.sleep(1 if system() != "Windows" else 5)  # let the server start

        yield openapi_url


@pytest.fixture(scope="session")
def weather_fastapi_openapi_url() -> Iterator[str]:
    yield from _create_fastapi_openapi_url(create_weather_fastapi_app)


@pytest.fixture(scope="session")
def google_sheets_fastapi_openapi_url() -> Iterator[str]:
    yield from _create_fastapi_openapi_url(create_google_sheet_fastapi_app)
