import httpx

from .conftest import find_free_port


def test_find_free_port() -> None:
    port = find_free_port()
    assert isinstance(port, int)
    assert 1024 <= port <= 65535


def test_weather_fastapi_openapi(weather_fastapi_openapi_url: str) -> None:
    assert isinstance(weather_fastapi_openapi_url, str)

    resp = httpx.get(weather_fastapi_openapi_url)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert "openapi" in resp_json
    assert "servers" in resp_json
    assert len(resp_json["servers"]) == 1
    assert resp_json["info"]["title"] == "Weather"
