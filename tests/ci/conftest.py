from typing import Any

import pytest


@pytest.fixture()
def patch_envs(monkeypatch: Any) -> None:  # noqa: PT004
    monkeypatch.setenv("AZURE_OPENAI_API_KEY_SWEDEN", "dummy_key")
    monkeypatch.setenv("AZURE_API_ENDPOINT", "dummy_endpoint")
    monkeypatch.setenv("AZURE_GPT4_MODEL", "airt-gpt4")
    monkeypatch.setenv("AZURE_GPT35_MODEL", "gpt-35-turbo-16k")
