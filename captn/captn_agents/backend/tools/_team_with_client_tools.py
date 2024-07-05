import httpx
from fastagency.openapi.client import Client

__all__ = ("create_client",)


def create_client(openapi_url: str) -> Client:
    with httpx.Client() as httpx_client:
        response = httpx_client.get(openapi_url)
        response.raise_for_status()
        openapi_spec = response.text

    client = Client.create(openapi_spec)

    return client
