import contextlib
import socket
import threading
import time
from platform import system
from typing import Annotated, Iterator

import pytest
import uvicorn
from fastapi import FastAPI, Path


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


@pytest.fixture(scope="session")
def weather_fastapi_openapi_url() -> Iterator[str]:
    host = "127.0.0.1"
    port = find_free_port()
    app = create_weather_fastapi_app(host, port)
    openapi_url = f"http://{host}:{port}/openapi.json"

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = Server(config=config)
    with server.run_in_thread():
        time.sleep(1 if system() != "Windows" else 5)  # let the server start

        yield openapi_url
