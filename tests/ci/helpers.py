import os
import unittest.mock
from contextlib import contextmanager
from typing import Any


@contextmanager
def mock_env() -> Any:
    DUMMY = "dummy"
    with unittest.mock.patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY_SWEDEN": DUMMY,
            "AZURE_API_ENDPOINT": DUMMY,
            "AZURE_API_VERSION": DUMMY,
            "AZURE_GPT4_MODEL": "airt-gpt4",
            "AZURE_GPT35_MODEL": "gpt-35-turbo-16k",
            "INFOBIP_API_KEY": DUMMY,
            "INFOBIP_BASE_URL": DUMMY,
        },
        clear=True,
    ):
        yield
