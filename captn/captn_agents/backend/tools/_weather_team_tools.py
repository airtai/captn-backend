import httpx
from fastagency.openapi.client import Client


def create_weather_team_client() -> Client:
    openapi_url = "https://weather.tools.fastagency.ai/openapi.json"

    with httpx.Client() as httpx_client:
        response = httpx_client.get(openapi_url)
        response.raise_for_status()
        openapi_spec = response.text

    client = Client.create(openapi_spec)

    return client
