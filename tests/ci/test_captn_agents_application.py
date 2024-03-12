import unittest
from tempfile import TemporaryDirectory
from typing import Dict

import autogen
import pytest
from autogen.cache import Cache
from autogen.io.websockets import IOStream, IOWebsockets
from httpx import Request, Response
from openai import BadRequestError
from websockets.sync.client import connect as ws_connect

from captn.captn_agents.application import on_connect
from captn.captn_agents.backend.config import config_list_gpt_3_5
from captn.captn_agents.backend.functions import TeamResponse

from .helpers import mock_env

with mock_env():
    from captn.captn_agents.application import (
        RETRY_MESSAGE,
        CaptnAgentRequest,
        _get_message,
        chat,
    )


def test_chat_when_openai_bad_request_is_raised() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.application.start_or_continue_conversation"
    ) as mock_start_or_continue_conversation:
        error_message = "Bad Request"
        request = Request(
            method="POST",
            url="",
        )
        response = Response(status_code=400, request=request)
        mock_start_or_continue_conversation.side_effect = BadRequestError(
            message=error_message, response=response, body=None
        )

        captn_request = CaptnAgentRequest(
            message="This is my task",
            user_id=-1,
            conv_id=-1,
            all_messages=[
                {
                    "role": "assistant",
                    "content": "Below is your daily analysis for 29-Jan-24\n\nYour campaigns have performed yesterday:\n - Clicks: 124 clicks (+3.12%)\n - Spend: $6.54 USD (-1.12%)\n - Cost per click: $0.05 USD (+12.00%)\n\n### Proposed User Action ###\n1. Remove 'Free' keyword because it is not performing well\n2. Increase budget from $10/day to $20/day\n3. Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'\n4. Select some or all of them",
                },
                {
                    "role": "user",
                    "content": "I want to Remove 'Free' keyword because it is not performing well",
                },
            ],
            agent_chat_history='[{"role": "agent", "content": "Conversation 1"},{"role": "agent", "content": "Conversation 2"},{"role": "agent", "content": "Conversation 3"}]',
            is_continue_daily_analysis=False,
        )
        with pytest.raises(BadRequestError):
            chat(request=captn_request)

        assert mock_start_or_continue_conversation.call_count == 2
        mock_start_or_continue_conversation.assert_has_calls(
            [
                unittest.mock.call(
                    user_id=-1,
                    conv_id=-1,
                    task="This is my task",
                    max_round=80,
                    human_input_mode="NEVER",
                    class_name="google_ads_team",
                ),
                unittest.mock.call(
                    user_id=-1,
                    conv_id=-1,
                    task=RETRY_MESSAGE,  # The second call is a retry message
                    max_round=80,
                    human_input_mode="NEVER",
                    class_name="google_ads_team",
                ),
            ]
        )


class TestConsoleIOWithWebsockets:
    @pytest.mark.skip(reason="Add AZURE keys to CI. After that, remove the skip.")
    def test_websockets_chat(self) -> None:
        print("Testing setup", flush=True)

        success_dict = {"success": False}

        def on_connect(
            iostream: IOWebsockets, success_dict: Dict[str, bool] = success_dict
        ) -> None:
            try:
                with IOStream.set_default(iostream):
                    print(
                        f" - on_connect(): Connected to client using IOWebsockets {iostream}",
                        flush=True,
                    )

                    print(" - on_connect(): Receiving message from client.", flush=True)

                    initial_msg = iostream.input()

                    llm_config = {
                        "config_list": config_list_gpt_3_5,
                        "stream": True,
                    }

                    agent = autogen.ConversableAgent(
                        name="chatbot",
                        system_message="Complete a task given to you and reply TERMINATE when the task is done.",
                        llm_config=llm_config,
                    )

                    # create a UserProxyAgent instance named "user_proxy"
                    user_proxy = autogen.UserProxyAgent(
                        name="user_proxy",
                        system_message="A proxy for the user.",
                        is_termination_msg=lambda x: x.get("content", "")
                        and x.get("content", "").rstrip().endswith("TERMINATE"),
                        human_input_mode="NEVER",
                        max_consecutive_auto_reply=10,
                        code_execution_config=False,
                    )

                    @user_proxy.register_for_execution()  # type: ignore[misc]
                    @agent.register_for_llm(description="Weather forecats for a city")  # type: ignore[misc]
                    def weather_forecast(city: str) -> str:
                        return f"The weather forecast for {city} is sunny."

                    # we will use a temporary directory as the cache path root to ensure fresh completion each time
                    with TemporaryDirectory() as cache_path_root:
                        with Cache.disk(cache_path_root=cache_path_root) as cache:
                            print(
                                f" - on_connect(): Initiating chat with agent {agent} using message '{initial_msg}'",
                                flush=True,
                            )
                            user_proxy.initiate_chat(  # noqa: F704
                                agent,
                                message=initial_msg,
                                cache=cache,
                            )

                    success_dict["success"] = True
                    return
            except Exception as e:
                print(f" - on_connect(): Exception occurred: {e}", flush=True)
                raise

        with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=8765) as uri:
            print(
                f" - test_setup() with websocket server running on {uri}.", flush=True
            )

            with ws_connect(uri) as websocket:
                print(f" - Connected to server on {uri}", flush=True)

                print(" - Sending message to server.", flush=True)
                # websocket.send("2+2=?")
                websocket.send(
                    "Please check the weather in Paris and write a poem about it."
                )

                while True:
                    message = websocket.recv()
                    message = (
                        message.decode("utf-8")
                        if isinstance(message, bytes)
                        else message
                    )
                    # drop the newline character
                    if message.endswith("\n"):
                        message = message[:-1]

                    print(message, end="", flush=True)

                    if "TERMINATE" in message:
                        print()
                        print(" - Received TERMINATE message. Exiting.", flush=True)
                        break

        assert success_dict["success"]
        print("Test passed.", flush=True)

    @pytest.mark.skip(reason="TODO: run the application, mock google ads functions...")
    def test_team_chat(self) -> None:
        print("Testing setup", flush=True)

        success_dict = {"success": False}

        with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=8765) as uri:
            print(
                f" - test_setup() with websocket server running on {uri}.", flush=True
            )

            request = CaptnAgentRequest(
                message="Business: airt.ai\nGoal: Increase brand awareness\nCurrent Situation: Running digital marketing campaigns\nWebsite: airt.ai\nDigital Marketing Objectives: Increase brand visibility, reach a wider audience, and improve brand recognition\nNext Steps: Analyze current Google Ads campaigns, identify opportunities for optimization, and create new strategies to increase brand awareness\nAny Other Information Related to Customer Brief: N/A",
                user_id=1,
                conv_id=1,
                all_messages=[
                    {
                        "role": "assistant",
                        "content": "Below is your daily analysis for 29-Jan-24\n\nYour campaigns have performed yesterday:\n - Clicks: 124 clicks (+3.12%)\n - Spend: $6.54 USD (-1.12%)\n - Cost per click: $0.05 USD (+12.00%)\n\n### Proposed User Action ###\n1. Remove 'Free' keyword because it is not performing well\n2. Increase budget from $10/day to $20/day\n3. Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'\n4. Select some or all of them",
                    },
                    {
                        "role": "user",
                        "content": "I want to Remove 'Free' keyword because it is not performing well",
                    },
                ],
                agent_chat_history='[{"role": "agent", "content": "Conversation 1"},{"role": "agent", "content": "Conversation 2"},{"role": "agent", "content": "Conversation 3"}]',
                is_continue_daily_analysis=False,
                retry=True,
            )
            with ws_connect(uri) as websocket:
                print(f" - Connected to server on {uri}", flush=True)

                print(" - Sending message to server.", flush=True)
                # websocket.send("2+2=?")
                websocket.send(request.model_dump_json())

                while True:
                    message = websocket.recv()
                    try:
                        team_response = TeamResponse.model_validate_json(message)
                        assert team_response.terminate_groupchat
                        return
                    except Exception:
                        pass

                    message = (
                        message.decode("utf-8")
                        if isinstance(message, bytes)
                        else message
                    )
                    # # drop the newline character
                    # if message.endswith("\n"):
                    #     message = message[:-1]

                    # print("This was the message: ")
                    print(message, end="", flush=True)

                    if "TERMINATE" in message:
                        print()
                        print(" - Received TERMINATE message. Exiting.", flush=True)
                        break

        assert success_dict["success"]
        print("Test passed.", flush=True)


def test_get_message_daily_analysis() -> None:

    request = CaptnAgentRequest(
        message="I want to Remove 'Free' keyword because it is not performing well",
        user_id=-1,
        conv_id=-1,
        all_messages=[
            {
                "role": "assistant",
                "content": "Below is your daily analysis for 29-Jan-24\n\nYour campaigns have performed yesterday:\n - Clicks: 124 clicks (+3.12%)\n - Spend: $6.54 USD (-1.12%)\n - Cost per click: $0.05 USD (+12.00%)\n\n### Proposed User Action ###\n1. Remove 'Free' keyword because it is not performing well\n2. Increase budget from $10/day to $20/day\n3. Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'\n4. Select some or all of them",
            },
            {
                "role": "user",
                "content": "I want to Remove 'Free' keyword because it is not performing well",
            },
        ],
        agent_chat_history='[{"role": "agent", "content": "Conversation 1"},{"role": "agent", "content": "Conversation 2"},{"role": "agent", "content": "Conversation 3"}]',
        is_continue_daily_analysis=False,
    )
    actual = _get_message(request)
    expected = """
### History ###
This is the JSON encoded history of your conversation that made the Daily Analysis and Proposed User Action. Please use this context and continue the execution according to the User Action:

[{"role": "agent", "content": "Conversation 1"},{"role": "agent", "content": "Conversation 2"},{"role": "agent", "content": "Conversation 3"}]

### Daily Analysis ###
Below is your daily analysis for 29-Jan-24

Your campaigns have performed yesterday:
 - Clicks: 124 clicks (+3.12%)
 - Spend: $6.54 USD (-1.12%)
 - Cost per click: $0.05 USD (+12.00%)

### Proposed User Action ###
1. Remove 'Free' keyword because it is not performing well
2. Increase budget from $10/day to $20/day
3. Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'
4. Select some or all of them

### User Action ###
I want to Remove 'Free' keyword because it is not performing well
"""
    assert actual == expected


def test_get_message_daily_analysis_continue() -> None:

    request = CaptnAgentRequest(
        message="I want to Remove 'Free' keyword because it is not performing well",
        user_id=-1,
        conv_id=-1,
        all_messages=[
            {
                "role": "assistant",
                "content": "Below is your daily analysis for 29-Jan-24\n\nYour campaigns have performed yesterday:\n - Clicks: 124 clicks (+3.12%)\n - Spend: $6.54 USD (-1.12%)\n - Cost per click: $0.05 USD (+12.00%)\n\n### Proposed User Action ###\n1. Remove 'Free' keyword because it is not performing well\n2. Increase budget from $10/day to $20/day\n3. Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'\n4. Select some or all of them",
            },
            {
                "role": "user",
                "content": "I want to Remove 'Free' keyword because it is not performing well",
            },
        ],
        agent_chat_history='[{"role": "agent", "content": "Conversation 1"},{"role": "agent", "content": "Conversation 2"},{"role": "agent", "content": "Conversation 3"}]',
        is_continue_daily_analysis=True,
    )
    actual = _get_message(request)
    expected = "I want to Remove 'Free' keyword because it is not performing well"
    assert actual == expected


def test_get_message_normal_chat() -> None:

    request = CaptnAgentRequest(
        message="I want to Remove 'Free' keyword because it is not performing well",
        user_id=-1,
        conv_id=-1,
        all_messages=[
            {
                "role": "assistant",
                "content": "Below is your daily analysis for 29-Jan-24\n\nYour campaigns have performed yesterday:\n - Clicks: 124 clicks (+3.12%)\n - Spend: $6.54 USD (-1.12%)\n - Cost per click: $0.05 USD (+12.00%)\n\n### Proposed User Action ###\n1. Remove 'Free' keyword because it is not performing well\n2. Increase budget from $10/day to $20/day\n3. Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'\n4. Select some or all of them",
            },
            {
                "role": "user",
                "content": "I want to Remove 'Free' keyword because it is not performing well",
            },
        ],
        agent_chat_history=None,
        is_continue_daily_analysis=False,
    )
    actual = _get_message(request)
    expected = "I want to Remove 'Free' keyword because it is not performing well"
    assert actual == expected


# def test_on_connect() -> None:
#     with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=8080) as uri:
#         print(f"Websocket server started at {uri}.", flush=True)
