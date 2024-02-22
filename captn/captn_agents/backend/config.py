import os

import openai
from autogen import __version__ as autogen_version
from autogen.oai.openai_utils import filter_config
from dotenv import load_dotenv

__all__ = ["CONFIG_LIST"]

load_dotenv()


api_key_sweden = os.getenv("AZURE_OPENAI_API_KEY_SWEDEN")
api_base_sweden = os.getenv("AZURE_API_ENDPOINT")
gpt_4_model_name = os.getenv("AZURE_GPT4_MODEL")
gpt_3_5_model_name = os.getenv("AZURE_GPT35_MODEL")

openai.api_type = "azure"
openai.api_version = "2023-12-01-preview"

CONFIG_LIST = [
    {
        "model": gpt_4_model_name,
        "api_key": api_key_sweden,
        "api_base": api_base_sweden,
        "base_url": api_base_sweden,
        "api_type": openai.api_type,
        "api_version": openai.api_version,
    },
    {
        "model": gpt_3_5_model_name,
        "api_key": api_key_sweden,
        "api_base": api_base_sweden,
        "base_url": api_base_sweden,
        "api_type": openai.api_type,
        "api_version": openai.api_version,
    },
]

for config in CONFIG_LIST:
    if autogen_version < "0.2.":
        config.pop("base_url")
    else:
        config.pop("api_base")
        # config.pop("api_type")

config_list_gpt_3_5 = filter_config(CONFIG_LIST, {"model": "gpt-35-turbo-16k"})
config_list_gpt_4 = filter_config(CONFIG_LIST, {"model": "airt-gpt4"})
