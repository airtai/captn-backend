import os
from typing import Dict, List, Optional

import openai
from autogen import __version__ as autogen_version
from autogen.oai.openai_utils import filter_config

__all__ = ("Config",)


class Config:
    def __init__(self) -> None:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_base = os.getenv("AZURE_API_ENDPOINT")
        self.gpt_4_model_name = os.getenv("AZURE_GPT4_MODEL")
        self.gpt_3_5_model_name = os.getenv("AZURE_GPT35_MODEL")

        api_key_gpt_4o = os.getenv("AZURE_OPENAI_API_KEY_GPT4O")
        api_base_gpt_4o = os.getenv("AZURE_API_ENDPOINT_GPT4O")
        self.gpt_4o_model_name = os.getenv("AZURE_GPT4O_MODEL")

        openai.api_type = "azure"
        openai.api_version = os.getenv("AZURE_API_VERSION")

        self.CONFIG_LIST = [
            {
                "model": self.gpt_4_model_name,
                "api_key": api_key,
                "api_base": api_base,
                "base_url": api_base,
                "api_type": openai.api_type,
                "api_version": openai.api_version,
            },
            {
                "model": self.gpt_3_5_model_name,
                "api_key": api_key,
                "api_base": api_base,
                "base_url": api_base,
                "api_type": openai.api_type,
                "api_version": openai.api_version,
            },
            {
                "model": self.gpt_4o_model_name,
                "api_key": api_key_gpt_4o,
                "api_base": api_base_gpt_4o,
                "base_url": api_base_gpt_4o,
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

    def get_config_list(self, model_name: Optional[str]) -> List[Dict[str, str]]:
        try:
            if not model_name:
                raise ValueError("Model name is required!")

            config_list: List[Dict[str, str]] = filter_config(
                self.CONFIG_LIST, {"model": model_name}
            )
        except Exception as e:
            print(f"Error: {e}")
            config_list = []

        return config_list

    @property
    def config_list_gpt_3_5(self) -> List[Dict[str, str]]:
        return self.get_config_list(self.gpt_3_5_model_name)

    @property
    def config_list_gpt_4(self) -> List[Dict[str, str]]:
        return self.get_config_list(self.gpt_4_model_name)

    @property
    def config_list_gpt_4o(self) -> List[Dict[str, str]]:
        return self.get_config_list(self.gpt_4o_model_name)
