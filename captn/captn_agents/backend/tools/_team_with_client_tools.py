import httpx
from fastagency.api.openapi.client import OpenAPI

__all__ = ("create_client",)


def create_client(openapi_url: str) -> OpenAPI:
    with httpx.Client() as httpx_client:
        response = httpx_client.get(openapi_url)
        response.raise_for_status()
        openapi_spec = response.text

    client = OpenAPI.create(openapi_spec)

    return client
