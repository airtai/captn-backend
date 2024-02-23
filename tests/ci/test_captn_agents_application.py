import unittest

import pytest
from httpx import Request, Response
from openai import BadRequestError


def test_chat_when_openai_bad_request_is_raised() -> None:
    from captn.captn_agents.application import RETRY_MESSAGE, CaptnAgentRequest, chat

    with unittest.mock.patch(
        "captn.captn_agents.application.start_conversation"
    ) as mock_start_conversation:
        error_message = "Bad Request"
        request = Request(
            method="POST",
            url="",
        )
        response = Response(status_code=400, request=request)
        mock_start_conversation.side_effect = BadRequestError(
            message=error_message, response=response, body=None
        )

        captn_request = CaptnAgentRequest(
            message="This is my task",
            user_id=-1,
            conv_id=-1,
        )
        with pytest.raises(BadRequestError):
            chat(request=captn_request)

        assert mock_start_conversation.call_count == 2
        mock_start_conversation.assert_has_calls(
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
