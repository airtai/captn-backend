from typing import Iterator

import autogen
import pytest

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.tools._weather_team_tools import (
    create_weather_team_client,
)
from captn.captn_agents.backend.tools.patch_client import (
    get_patch_patch_register_for_execution,
)


class TestPatchClient:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }

    @pytest.mark.flaky
    @pytest.mark.openai
    def test_patch_client(self, weather_fastapi_openapi_url: str) -> None:
        client = create_weather_team_client(weather_fastapi_openapi_url)

        kwargs_to_patch = {
            "city": "San Francisco",
        }
        get_patch_patch_register_for_execution(
            client, kwargs_to_patch=kwargs_to_patch
        )()

        assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config=self.llm_config,
        )

        user_proxy = autogen.UserProxyAgent(name="user_proxy", human_input_mode="NEVER")

        client.register_for_llm(assistant)
        client.register_for_execution(user_proxy)

        user_proxy.initiate_chat(
            assistant,
            message="What is the weather in London? Once the weather is known, please write 'TERMINATE' to end the conversation.",
        )

        messages = assistant.chat_messages[user_proxy]
        success = False
        for message in messages:
            if "tool_responses" in message:
                assert (
                    message["content"] == "Weather in San Francisco is sunny"
                ), message
                success = True
                break

        assert success
