from typing import Any, Dict

import pytest
import requests


class DummyResponse:
    def __init__(self, status_code: int, d: Dict[str, Any], **kwargs) -> None:  # type: ignore [no-untyped-def]
        self.status_code = status_code
        self.d = d
        self.ok = True if status_code == 200 else False

    def json(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return self.d


@pytest.fixture
def set_env_variables(monkeypatch):  # type: ignore [no-untyped-def]
    monkeypatch.setenv("INFOBIP_API_KEY", "123")
    monkeypatch.setenv("INFOBIP_BASE_URL", "dummy.base.com")


@pytest.fixture
def mock_response(monkeypatch, status_code, response_data):  # type: ignore [no-untyped-def]
    def _mock_response(*args, **kwargs):  # type: ignore [no-untyped-def]
        return DummyResponse(status_code=status_code, d=response_data)

    monkeypatch.setattr(requests, "post", _mock_response)


@pytest.mark.parametrize(
    "status_code, response_data, expected_exception",
    [
        (
            200,
            {
                "bulkId": "t3j7tho5rk69t2f3bruh",
                "messages": [
                    {
                        "to": "test@airt.ai",
                        "messageId": "692g3652bq2tpvps2nk2",
                        "status": {
                            "groupId": 1,
                            "groupName": "PENDING",
                            "id": 26,
                            "name": "PENDING_ACCEPTED",
                            "description": "Message accepted, pending for delivery.",
                        },
                    }
                ],
            },
            None,
        ),
        (
            500,
            {
                "bulkId": "t3j7tho5rk69t2f3bruh",
                "messages": [
                    {
                        "to": "test@airt.ai",
                        "messageId": "692g3652bq2tpvps2nk2",
                        "status": {
                            "groupId": 1,
                            "groupName": "PENDING",
                            "id": 26,
                            "name": "REJECTED",
                            "description": "Message rejected.",
                        },
                    }
                ],
            },
            "Failed to send email: 500",
        ),
    ],
)
def test_send_email(  # type: ignore [no-untyped-def]
    set_env_variables,
    mock_response,
    status_code,
    response_data,
    expected_exception,
):
    from captn.email import send_email

    if expected_exception:
        with pytest.raises(Exception) as exc_info:
            send_email(
                to_email="test@airt.ai", subject="Hi there!", body_text="It is me, SDK!"
            )

        assert expected_exception in str(exc_info.value)
    else:
        response = send_email(
            to_email="test@airt.ai", subject="Hi there!", body_text="It is me, SDK!"
        )
        assert response == response_data
