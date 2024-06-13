import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Dict

import autogen
import pytest
from autogen.io.websockets import IOWebsockets
from fastapi import HTTPException
from fastapi.testclient import TestClient
from websockets.sync.client import connect as ws_connect

from captn.captn_agents.application import (
    ON_FAILURE_MESSAGE,
    CaptnAgentRequest,
    _get_message,
    on_connect,
    router,
)
from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.tools._functions import TeamResponse


class TestConsoleIOWithWebsockets:
    @pytest.fixture()
    def setup(self) -> None:
        self.request = CaptnAgentRequest(
            message="Business: airt.ai\nGoal: Increase brand awareness\nCurrent Situation: Running digital marketing campaigns\nWebsite: airt.ai\nDigital Marketing Objectives: Increase brand visibility, reach a wider audience, and improve brand recognition\nNext Steps: Analyze current Google Ads campaigns, identify opportunities for optimization, and create new strategies to increase brand awareness\nAny Other Information Related to Customer Brief: N/A",
            user_id=1,
            conv_id=1,
            all_messages=[
                {
                    "role": "assistant",
                    "content": "Below is your weekly analysis for 29-Jan-24\n\nYour campaigns have performed yesterday:\n - Clicks: 124 clicks (+3.12%)\n - Spend: $6.54 USD (-1.12%)\n - Cost per click: $0.05 USD (+12.00%)\n\n### Proposed User Action ###\n1. Remove 'Free' keyword because it is not performing well\n2. Increase budget from $10/day to $20/day\n3. Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'\n4. Select some or all of them",
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

    @pytest.mark.openai
    def test_websockets_chat(self) -> None:
        print("Testing setup", flush=True)

        success_dict = {"success": False}

        def on_connect(
            iostream: IOWebsockets, success_dict: Dict[str, bool] = success_dict
        ) -> None:
            try:
                print(
                    f" - on_connect(): Connected to client using IOWebsockets {iostream}",
                    flush=True,
                )

                print(" - on_connect(): Receiving message from client.", flush=True)

                initial_msg = iostream.input()

                config = Config()

                llm_config = {
                    "config_list": config.config_list_gpt_3_5,
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
                    return (
                        f"The weather forecast for {city} at {datetime.now()} is sunny."
                    )

                print(
                    f" - on_connect(): Initiating chat with agent {agent} using message '{initial_msg}'",
                    flush=True,
                )
                user_proxy.initiate_chat(  # noqa: F704
                    agent,
                    message=initial_msg,
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

                    print(message, end="", flush=True)

                    if "TERMINATE" in message:
                        print()
                        print(" - Received TERMINATE message. Exiting.", flush=True)
                        break

        assert success_dict["success"]
        print("Test passed.", flush=True)

    @pytest.mark.skip(reason="TODO: run the application, mock google ads functions...")
    def test_team_chat(self, setup: Callable[[None], None]) -> None:
        print("Testing setup", flush=True)

        success_dict = {"success": False}

        with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=8765) as uri:
            print(
                f" - test_setup() with websocket server running on {uri}.", flush=True
            )

            with ws_connect(uri) as websocket:
                print(f" - Connected to server on {uri}", flush=True)

                print(" - Sending message to server.", flush=True)
                # websocket.send("2+2=?")
                websocket.send(self.request.model_dump_json())

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

    def test_try_to_continue_the_conversation_on_exceptions(
        self, setup: Callable[[None], None]
    ) -> None:
        print("Testing setup", flush=True)

        success_dict = {"success": False}

        with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=8765) as uri:
            print(
                f" - test_setup() with websocket server running on {uri}.", flush=True
            )

            with ws_connect(uri) as websocket:
                # mock start_or_continue_conversation
                with unittest.mock.patch(
                    "captn.captn_agents.application.start_or_continue_conversation"
                ) as mock_start_or_continue_conversation:
                    mock_start_or_continue_conversation.side_effect = [
                        Exception("Error"),
                        (None, "TERMINATE"),
                    ]
                    print(f" - Connected to server on {uri}", flush=True)

                    print(" - Sending message to server.", flush=True)
                    websocket.send(self.request.model_dump_json())

                    while True:
                        message = websocket.recv()

                        message = (
                            message.decode("utf-8")
                            if isinstance(message, bytes)
                            else message
                        )

                        if "TERMINATE" in message:
                            print()
                            print(" - Received TERMINATE message. Exiting.", flush=True)
                            success_dict["success"] = True
                            break

        message = _get_message(self.request)
        mock_start_or_continue_conversation.assert_has_calls(
            [
                unittest.mock.call(
                    user_id=1,
                    conv_id=1,
                    task=message,
                    max_round=80,
                    registred_team_name="default_team",
                ),
                unittest.mock.call(
                    user_id=1,
                    conv_id=1,
                    task=message,
                    max_round=80,
                    registred_team_name="default_team",
                ),
            ]
        )
        assert success_dict["success"]
        print("Test passed.", flush=True)

    def test_on_connect_prometheus_error_logging(
        self, setup: Callable[[None], None]
    ) -> None:
        with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=8765) as uri:
            print(
                f" - test_setup() with websocket server running on {uri}.", flush=True
            )

            with ws_connect(uri) as websocket:
                with (
                    unittest.mock.patch(
                        "captn.captn_agents.application.start_or_continue_conversation"
                    ) as mock_start_or_continue_conversation,
                    unittest.mock.patch(
                        "captn.captn_agents.application.THREE_IN_A_ROW_EXCEPTIONS"
                    ) as mock_three_in_a_row_exceptions,
                    unittest.mock.patch(
                        "captn.captn_agents.application.REGULAR_EXCEPTIONS"
                    ) as mock_regular_exceptions,
                    unittest.mock.patch(
                        "captn.captn_agents.application.INVALID_MESSAGE_IN_IOSTREAM"
                    ) as mock_invalid_message_in_iostream,
                    unittest.mock.patch(
                        "captn.captn_agents.application.RANDOM_EXCEPTIONS"
                    ) as mock_random_exceptions,
                ):
                    mock_start_or_continue_conversation.side_effect = (
                        Exception("Error 1"),
                        Exception("Error 2"),
                        Exception("Error 3"),
                    )

                    print(f" - Connected to server on {uri}", flush=True)

                    print(" - Sending message to server.", flush=True)

                    websocket.send(self.request.model_dump_json())

                    while True:
                        message = websocket.recv()

                        message = (
                            message.decode("utf-8")
                            if isinstance(message, bytes)
                            else message
                        )
                        if ON_FAILURE_MESSAGE in message:
                            print()
                            print(
                                " - Received ON_FAILURE_MESSAGE. Exiting.", flush=True
                            )

                            break

                    assert mock_three_in_a_row_exceptions.inc.call_count == 1
                    assert mock_regular_exceptions.inc.call_count == 3
                    mock_invalid_message_in_iostream.assert_not_called()
                    mock_random_exceptions.assert_not_called()


def test_get_message_weekly_analysis() -> None:
    request = CaptnAgentRequest(
        message="I want to Remove 'Free' keyword because it is not performing well",
        user_id=-1,
        conv_id=-1,
        all_messages=[
            {
                "role": "assistant",
                "content": "Below is your weekly analysis for 29-Jan-24\n\nYour campaigns have performed yesterday:\n - Clicks: 124 clicks (+3.12%)\n - Spend: $6.54 USD (-1.12%)\n - Cost per click: $0.05 USD (+12.00%)\n\n### Proposed User Action ###\n1. Remove 'Free' keyword because it is not performing well\n2. Increase budget from $10/day to $20/day\n3. Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'\n4. Select some or all of them",
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
This is the JSON encoded history of your conversation that made the Weekly Analysis and Proposed User Action. Please use this context and continue the execution according to the User Action:

[{"role": "agent", "content": "Conversation 1"},{"role": "agent", "content": "Conversation 2"},{"role": "agent", "content": "Conversation 3"}]

### Weekly Analysis ###
Below is your weekly analysis for 29-Jan-24

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


def test_get_message_weekly_analysis_continue() -> None:
    request = CaptnAgentRequest(
        message="I want to Remove 'Free' keyword because it is not performing well",
        user_id=-1,
        conv_id=-1,
        all_messages=[
            {
                "role": "assistant",
                "content": "Below is your weekly analysis for 29-Jan-24\n\nYour campaigns have performed yesterday:\n - Clicks: 124 clicks (+3.12%)\n - Spend: $6.54 USD (-1.12%)\n - Cost per click: $0.05 USD (+12.00%)\n\n### Proposed User Action ###\n1. Remove 'Free' keyword because it is not performing well\n2. Increase budget from $10/day to $20/day\n3. Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'\n4. Select some or all of them",
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
                "content": "Below is your weekly analysis for 29-Jan-24\n\nYour campaigns have performed yesterday:\n - Clicks: 124 clicks (+3.12%)\n - Spend: $6.54 USD (-1.12%)\n - Cost per click: $0.05 USD (+12.00%)\n\n### Proposed User Action ###\n1. Remove 'Free' keyword because it is not performing well\n2. Increase budget from $10/day to $20/day\n3. Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'\n4. Select some or all of them",
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


class TestUploadFile:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.client = TestClient(router)
        self.data = {
            "user_id": 123,
            "conv_id": 456,
        }

    def test_upload_file_raises_exception_if_invalid_content_type(self):
        # Create a dummy file
        file_content = b"Hello, world!"
        file_name = "test.txt"
        files = {"file": (file_name, file_content, "text/plain")}

        # Send a POST request to the upload endpoint
        with pytest.raises(HTTPException) as exc_info:
            self.client.post("/uploadfile/", files=files, data=self.data)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid file content type"

    @pytest.mark.parametrize(
        "file_content, success",
        [
            (
                b"from_destination,to_destination,additional_column\nvalue1,value2,value3",
                True,
            ),
            (b"from_destination,additional_column\nvalue1,value3", False),
        ],
    )
    def test_upload_csv_file(self, file_content: bytes, success: bool):
        # Create a dummy CSV file
        file_content = file_content
        file_name = "test.csv"
        files = {"file": (file_name, file_content, "text/csv")}

        with TemporaryDirectory() as tmp_dir:
            with unittest.mock.patch(
                "captn.captn_agents.application.UPLOADED_FILES_DIR",
                Path(tmp_dir),
            ) as mock_uploaded_files_dir:
                file_path = (
                    mock_uploaded_files_dir
                    / str(self.data["user_id"])
                    / str(self.data["conv_id"])
                    / file_name
                )

                if success:
                    response = self.client.post(
                        "/uploadfile/", files=files, data=self.data
                    )
                    assert response.status_code == 200
                    assert response.json() == {"filename": file_name}
                    # Check if the file was saved
                    assert file_path.exists()
                    with open(file_path, "rb") as f:
                        assert f.read() == file_content
                else:
                    with pytest.raises(HTTPException) as exc_info:
                        self.client.post("/uploadfile/", files=files, data=self.data)
                    assert not file_path.exists()
                    assert (
                        exc_info.value.detail
                        == "Missing mandatory columns: to_destination"
                    )
