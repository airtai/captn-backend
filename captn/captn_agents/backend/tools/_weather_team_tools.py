import httpx
from fastagency.openapi.client import Client

from ..toolboxes import Toolbox
from ._functions import REPLY_TO_CLIENT_DESCRIPTION, BaseContext, reply_to_client

__all__ = (
    "create_weather_team_client",
    "create_weather_team_toolbox",
)


def create_weather_team_client(openapi_url: str) -> Client:
    with httpx.Client() as httpx_client:
        response = httpx_client.get(openapi_url)
        response.raise_for_status()
        openapi_spec = response.text

    client = Client.create(openapi_spec)

    return client


def create_weather_team_toolbox(
    user_id: int,
    conv_id: int,
) -> Toolbox:
    toolbox = Toolbox()

    context = BaseContext(
        user_id=user_id,
        conv_id=conv_id,
    )
    toolbox.set_context(context)

    toolbox.add_function(REPLY_TO_CLIENT_DESCRIPTION)(reply_to_client)

    return toolbox
