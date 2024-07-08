import contextlib
import socket
import threading
import time
from platform import system
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
)

import pytest
import uvicorn
from fastapi import Body, FastAPI, Path, Query, Response, status
from fastapi.responses import RedirectResponse
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
    base_url = f"http://{host}:{port}"
    app = FastAPI(
        title="Google Sheet",
        servers=[{"url": base_url, "description": "Local development server"}],
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

    @app.get("/login/success", description="Get the success message after login")
    def get_login_success() -> Dict[str, str]:
        return {"login_success": "You have successfully logged in"}

    @app.get("/login/callback")
    async def login_callback(
        code: Annotated[
            Optional[str],
            Query(description="The authorization code received after successful login"),
        ] = None,
        state: Annotated[Optional[str], Query(description="State")] = None,
    ) -> RedirectResponse:
        return RedirectResponse(url=f"{base_url}/login/success")

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
        return GoogleSheetValues(
            values=[
                ["Country", "Station From", "Station To"],
                ["USA", "New York", "Los Angeles"],
            ]
        )

    @app.post(
        "/update-sheet",
        description="Update data in a Google Sheet within the existing spreadsheet",
    )
    def update_sheet(
        user_id: Annotated[
            int, Query(description="The user ID for which the data is requested")
        ] = None,
        spreadsheet_id: Annotated[
            Optional[str],
            Query(description="ID of the Google Sheet to fetch data from"),
        ] = None,
        title: Annotated[
            Optional[str],
            Query(description="The title of the sheet to update"),
        ] = None,
        sheet_values: Annotated[
            Optional[GoogleSheetValues],
            Body(embed=True, description="Values to be written to the Google Sheet"),
        ] = None,
    ) -> Response:
        return Response(
            status_code=status.HTTP_200_OK,
            content=f"Sheet with the name '{title}' has been updated successfully.",
        )

    @app.post(
        "/create-sheet",
        description="Create a new Google Sheet within the existing spreadsheet",
    )
    def create_sheet(
        user_id: Annotated[
            int, Query(description="The user ID for which the data is requested")
        ],
        spreadsheet_id: Annotated[
            Optional[str],
            Query(description="ID of the Google Sheet to fetch data from"),
        ] = None,
        title: Annotated[
            Optional[str],
            Query(description="The title of the new sheet"),
        ] = None,
    ) -> Response:
        return Response(
            status_code=status.HTTP_201_CREATED,
            content=f"Sheet with the name '{title}' has been created successfully.",
        )

    @app.get(
        "/get-all-file-names", description="Get all sheets associated with the user"
    )
    def get_all_file_names(
        user_id: Annotated[
            int, Query(description="The user ID for which the data is requested")
        ],
    ) -> Dict[str, str]:
        return {
            "fabdbdfw1233": "Captn-template",
            "fabdbdfw1234": "New-routes",
            "fabdbdfw1235": "My file",
        }

    @app.get(
        "/get-all-sheet-titles",
        description="Get all sheet titles within a Google Spreadsheet",
    )
    def get_all_sheet_titles(
        user_id: Annotated[
            int, Query(description="The user ID for which the data is requested")
        ],
        spreadsheet_id: Annotated[
            Optional[str],
            Query(description="ID of the Google Sheet to fetch data from"),
        ] = None,
    ) -> List[str]:
        if spreadsheet_id == "fabdbdfw1233":
            return ["Keywords", "Ads"]
        elif spreadsheet_id == "fabdbdfw1234":
            return ["New"]
        return ["Sheet1", "Sheet2", "Sheet3"]

    @app.post(
        "/process-data",
        description="Process data to generate new ads or keywords based on the template",
    )
    def process_data(
        template_sheet_values: Annotated[
            Optional[GoogleSheetValues],
            Body(
                embed=True,
                description="Template values to be used for generating new ads or keywords",
            ),
        ] = None,
        new_campaign_sheet_values: Annotated[
            Optional[GoogleSheetValues],
            Body(
                embed=True,
                description="New campaign values to be used for generating new ads or keywords",
            ),
        ] = None,
        target_resource: Annotated[
            Optional[str],
            Query(
                description="The target resource to be updated. This can be 'ad' or 'keyword'"
            ),
        ] = None,
    ) -> GoogleSheetValues:
        return GoogleSheetValues(
            values=[
                ["Ad ID", "Ad Text", "Ad URL"],
                ["1", "Ad 1", "https://example.com/ad1"],
                ["2", "Ad 2", "https://example.com/ad2"],
            ]
        )

    @app.post(
        "/process-spreadsheet",
        description="Process data to generate new ads or keywords based on the template",
    )
    def process_spreadsheet(
        user_id: Annotated[
            int, Query(description="The user ID for which the data is requested")
        ],
        template_spreadsheet_id: Annotated[
            Optional[str],
            Query(description="ID of the Google Sheet with the template data"),
        ] = None,
        template_sheet_title: Annotated[
            Optional[str],
            Query(description="The title of the sheet with the template data"),
        ] = None,
        new_campaign_spreadsheet_id: Annotated[
            Optional[str],
            Query(description="ID of the Google Sheet with the new campaign data"),
        ] = None,
        new_campaign_sheet_title: Annotated[
            Optional[str],
            Query(description="The title of the sheet with the new campaign data"),
        ] = None,
        target_resource: Annotated[
            Optional[str],
            Query(
                description="The target resource to be updated, options: 'ad' or 'keyword'"
            ),
        ] = None,
    ) -> Response:
        return Response(
            status_code=status.HTTP_201_CREATED,
            content=f"Sheet with the name 'Captn - {target_resource.capitalize()}s' has been created successfully.",
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
