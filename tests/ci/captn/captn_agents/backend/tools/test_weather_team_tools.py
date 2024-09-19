import unittest
from pathlib import Path
from typing import Iterator
from unittest.mock import MagicMock

import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.teams._team import Team
from captn.captn_agents.backend.tools._team_with_client_tools import create_client
from captn.captn_agents.backend.tools._weather_team_tools import (
    create_weather_team_toolbox,
)

from .helpers import check_llm_config_descriptions, check_llm_config_total_tools


class TestTools:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }

        self.toolbox = create_weather_team_toolbox(
            user_id=12345,
            conv_id=67890,
            kwargs={},
        )

        yield
        Team._teams.clear()

    def test_llm_config(self) -> None:
        agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        user_proxy = UserProxyAgent(name="user_proxy", code_execution_config=False)

        self.toolbox.add_to_agent(agent, user_proxy)

        llm_config = agent.llm_config
        name_desc_dict = {
            "reply_to_client": "Respond to the client",
        }

        check_llm_config_total_tools(llm_config, 1)
        check_llm_config_descriptions(llm_config, name_desc_dict)


class TestClient:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }

        path = Path(__file__).parent / "fixtures" / "weather_openapi.json"
        with Path.open(path, "r") as f:
            weather_openapi_text = f.read()

        with unittest.mock.patch("httpx.Client.get") as mock_httpx_get:
            mock_response = MagicMock()
            mock_response.text = weather_openapi_text
            mock_response.raise_for_status.return_value = None

            mock_httpx_get.return_value = mock_response

            self.client = create_client("https://weather.com/openapi.json")

        yield
        Team._teams.clear()

    def test_llm_config(self) -> None:
        agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        user_proxy = UserProxyAgent(name="user_proxy", code_execution_config=False)

        self.client._register_for_execution(user_proxy)
        self.client._register_for_llm(agent)

        llm_config = agent.llm_config
        name_desc_dict = {
            "get_weather__get": "Get weather forecast for a given city",
        }

        check_llm_config_total_tools(llm_config, 1)
        check_llm_config_descriptions(llm_config, name_desc_dict)
