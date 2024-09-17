from typing import Dict, List

import autogen
import pytest

from captn.captn_agents.backend.tools._team_with_client_tools import create_client
from captn.captn_agents.backend.tools.patch_client import (
    get_patch_register_for_execution,
)


class TestGoogleSheets:
    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.fastapi_openapi_team
    def test_google_sheets_fastapi_openapi(
        self,
        llm_config: Dict[str, List[Dict[str, str]]],
        google_sheets_fastapi_openapi_url: str,
    ) -> None:
        client = create_client(google_sheets_fastapi_openapi_url)

        assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config=llm_config,
            system_message="Write 'TERMINATE' to terminate the conversation.",
        )

        user_proxy = autogen.UserProxyAgent(name="user_proxy", human_input_mode="NEVER")

        kwargs_to_patch = {
            "user_id": 2525,
        }
        get_patch_register_for_execution(client, kwargs_to_patch)()
        client._register_for_llm(assistant)
        client._register_for_execution(user_proxy)

        user_proxy.initiate_chat(
            assistant,
            message="""When sending requests to the Google Sheets API, use user_id=-1.
I want to get the URL to log in with Google.
I want to get the data from the Google spreadsheet id: 1234, title: 'New'.
Once the data is received write 'TERMINATE'""",
        )

        messages = assistant.chat_messages[user_proxy]
        expected = '{"values": [["Country", "Station From", "Station To"], ["USA", "New York", "Los Angeles"]]}'
        success = False
        for message in messages:
            if message["content"] == expected:
                success = True
                break
        assert success, "Expected message not found"
