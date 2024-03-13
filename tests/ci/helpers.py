import os
import unittest.mock
from contextlib import contextmanager
from typing import Any, Dict


def get_mocked_azure_env() -> Dict[str, str]:
    return {
        "AZURE_OPENAI_API_KEY_SWEDEN": "dummy",
        "AZURE_API_ENDPOINT": "dummy",
        "AZURE_API_VERSION": "dummy",
        "AZURE_GPT4_MODEL": "airt-gpt4",
        "AZURE_GPT35_MODEL": "gpt-35-turbo-16k",
    }


@contextmanager
def mock_env(mock_azure_env: bool = True) -> Any:
    DUMMY = "dummy"
    env_dict = {
        "INFOBIP_API_KEY": DUMMY,
        "INFOBIP_BASE_URL": DUMMY,
    }
    if mock_azure_env:
        env_dict.update(get_mocked_azure_env())

    with unittest.mock.patch.dict(
        os.environ,
        env_dict,
    ):
        yield
