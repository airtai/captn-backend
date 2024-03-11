import os
import unittest

import pytest
from autogen.io.websockets import IOWebsockets
from httpx import Request, Response
from openai import BadRequestError
from websockets.sync.client import connect as ws_connect

DUMMY = "dummy"
with unittest.mock.patch.dict(
    os.environ,
    {
        "AZURE_OPENAI_API_KEY_SWEDEN": DUMMY,
        "AZURE_API_ENDPOINT": DUMMY,
        "AZURE_API_VERSION": DUMMY,
        "AZURE_GPT4_MODEL": DUMMY,
        "AZURE_GPT35_MODEL": DUMMY,
        "INFOBIP_API_KEY": DUMMY,
        "INFOBIP_BASE_URL": DUMMY,
    },
):
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
                    iostream=None,
                ),
                unittest.mock.call(
                    user_id=-1,
                    conv_id=-1,
                    task=RETRY_MESSAGE,  # The second call is a retry message
                    max_round=80,
                    human_input_mode="NEVER",
                    class_name="google_ads_team",
                    iostream=None,
                ),
            ]
        )


class TestConsoleIOWithWebsockets:
    def test_input_print(self) -> None:
        print()
        print("Testing input/print", flush=True)

        def on_connect(iostream: IOWebsockets) -> None:
            print(
                f" - on_connect(): Connected to client using IOWebsockets {iostream}",
                flush=True,
            )

            print(" - on_connect(): Receiving message from client.", flush=True)

            msg = iostream.input()

            print(f" - on_connect(): Received message '{msg}' from client.", flush=True)

            assert msg == "Hello world!"

            for msg in ["Hello, World!", "Over and out!"]:
                print(
                    f" - on_connect(): Sending message '{msg}' to client.", flush=True
                )

                iostream.print(msg)

            print(" - on_connect(): Receiving message from client.", flush=True)

            msg = iostream.input("May I?")

            print(f" - on_connect(): Received message '{msg}' from client.", flush=True)
            assert msg == "Yes"

            return

        with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=8765) as uri:
            print(
                f" - test_setup() with websocket server running on {uri}.", flush=True
            )

            with ws_connect(uri) as websocket:
                print(f" - Connected to server on {uri}", flush=True)

                print(" - Sending message to server.", flush=True)
                websocket.send("Hello world!")

                for expected in ["Hello, World!", "Over and out!", "May I?"]:
                    print(" - Receiving message from server.", flush=True)
                    message = websocket.recv()
                    message = (
                        message.decode("utf-8")
                        if isinstance(message, bytes)
                        else message
                    )
                    # drop the newline character
                    if message.endswith("\n"):
                        message = message[:-1]

                    print(
                        f"   - Asserting received message '{message}' is the same as the expected message '{expected}'",
                        flush=True,
                    )
                    assert message == expected

                print(" - Sending message 'Yes' to server.", flush=True)
                websocket.send("Yes")

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
