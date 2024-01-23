import os

import openai
from autogen import __version__ as autogen_version
from autogen.oai.openai_utils import filter_config
from dotenv import load_dotenv

__all__ = ["CONFIG_LIST"]

load_dotenv()


litellm_model = os.getenv("LITELLM_MODEL")
litellm_api_base = os.getenv("LITELLM_API_BASE")

api_key_sweeden = os.getenv("AZURE_OPENAI_API_KEY_SWEEDEN")
api_base_sweeden = "https://airt-openai-sweden.openai.azure.com/"

api_key_canada = os.getenv("AZURE_OPENAI_API_KEY_CANADA")
api_base_canada = "https://airt-openai-canada.openai.azure.com/"

api_key_openai = os.getenv("OPENAI_API_KEY")

api_key_litellm = os.getenv("LITELLM_API_KEY")

openai.api_type = "azure"

openai.api_version = "2023-12-01-preview"

CONFIG_LIST = [
    # {
    #     "model": litellm_model,
    #     "api_base": litellm_api_base,
    #     "base_url": litellm_api_base,  # litellm compatible endpoint
    #     # "api_type": "open_ai",
    #     "api_key": api_key_litellm,  # just a placeholder
    # },
    # {
    #     "model": "airt-canada-gpt4",
    #     "api_base": "http://localhost:9055",
    #     "base_url": "http://localhost:9055",  #litellm compatible endpoint
    #     "api_type": "open_ai",
    #     "api_key": "NULL", # just a placeholder  # pragma: allowlist secret
    # },
    {
        "model": "airt-gpt4",
        "api_key": api_key_sweeden,
        "api_base": api_base_sweeden,
        "base_url": api_base_sweeden,
        "api_type": openai.api_type,
        "api_version": openai.api_version,
    },
    {
        "model": "gpt-35-turbo-16k",
        "api_key": api_key_sweeden,
        "api_base": api_base_sweeden,
        "base_url": api_base_sweeden,
        "api_type": openai.api_type,
        "api_version": openai.api_version,
    },
    # {
    #     "model": "gpt-4",
    #     "api_key": api_key_canada,
    #     "api_base": api_base_canada,
    #     "api_type": openai.api_type,
    #     "api_version": openai.api_version,
    #     "engine": "airt-canada-gpt4",
    # },
    # DO NOT USE OPENAI FOR NOW
    # {
    #     # "model": "gpt-4-1106-preview",
    #     "model": "gpt-4",
    #     "api_key": api_key_openai,
    # },
]

for config in CONFIG_LIST:
    if autogen_version < "0.2.":
        config.pop("base_url")
    else:
        config.pop("api_base")
        # config.pop("api_type")

config_list_gpt_3_5 = filter_config(CONFIG_LIST, {"model": "gpt-35-turbo-16k"})
config_list_gpt_4 = filter_config(CONFIG_LIST, {"model": "airt-gpt4"})
