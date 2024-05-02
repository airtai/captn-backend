import os
from typing import Dict, List

import openai
from autogen import __version__ as autogen_version
from autogen.oai.openai_utils import filter_config

__all__ = ("Config",)


class Config:
    def __init__(self) -> None:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_base = os.getenv("AZURE_API_ENDPOINT")
        gpt_4_model_name = os.getenv("AZURE_GPT4_MODEL")
        gpt_3_5_model_name = os.getenv("AZURE_GPT35_MODEL")

        openai.api_type = "azure"
        openai.api_version = os.getenv("AZURE_API_VERSION")

        self.CONFIG_LIST = [
            {
                "model": gpt_4_model_name,
                "api_key": api_key,
                "api_base": api_base,
                "base_url": api_base,
                "api_type": openai.api_type,
                "api_version": openai.api_version,
            },
            {
                "model": gpt_3_5_model_name,
                "api_key": api_key,
                "api_base": api_base,
                "base_url": api_base,
                "api_type": openai.api_type,
                "api_version": openai.api_version,
            },
        ]

        for config in self.CONFIG_LIST:
            if autogen_version < "0.2.":
                config.pop("base_url")
            else:
                config.pop("api_base")
                # config.pop("api_type")

    @property
    def config_list_gpt_3_5(self) -> List[Dict[str, str]]:
        try:
            config_list: List[Dict[str, str]] = filter_config(
                self.CONFIG_LIST, {"model": "gpt-35-turbo-16k"}
            )
        except Exception as e:
            print(f"Error: {e}")
            config_list = []

        return config_list

    @property
    def config_list_gpt_4(self) -> List[Dict[str, str]]:
        try:
            config_list: List[Dict[str, str]] = filter_config(
                self.CONFIG_LIST, {"model": "airt-gpt4"}
            )
        except Exception as e:
            print(f"Error: {e}")
            config_list = []

        return config_list
