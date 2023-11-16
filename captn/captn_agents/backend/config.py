import os

import openai
from dotenv import load_dotenv

__all__ = ["CONFIG_LIST"]

load_dotenv()

api_key_sweeden = os.getenv("AZURE_OPENAI_API_KEY_SWEEDEN")
api_base_sweeden = "https://airt-openai-sweden.openai.azure.com/"

api_key_canada = os.getenv("AZURE_OPENAI_API_KEY_CANADA")
api_base_canada = "https://airt-openai-canada.openai.azure.com/"

api_key_openai = os.getenv("OPENAI_API_KEY")

openai.api_type = "azure"

openai.api_version = "2023-07-01-preview"

CONFIG_LIST = [
    {
        "model": "gpt-4",
        "api_key": api_key_sweeden,
        "api_base": api_base_sweeden,
        "api_type": openai.api_type,
        "api_version": openai.api_version,
        "engine": "airt-gpt4",
    },
    {
        "model": "gpt-4",
        "api_key": api_key_canada,
        "api_base": api_base_canada,
        "api_type": openai.api_type,
        "api_version": openai.api_version,
        "engine": "airt-canada-gpt4",
    },
    # {
    #     # "model": "gpt-4-1106-preview",
    #     "model": "gpt-4",
    #     "api_key": api_key_openai,
    # },
]
