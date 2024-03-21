from typing import Any, Callable, Dict, Optional

import pytest
import requests


class DummyResponse:
    def __init__(self, status_code: int, d: Dict[str, Any], **kwargs: Any) -> None:
        self.status_code = status_code
        self.d = d
        self.ok = True if status_code == 200 else False

    def json(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self.d


@pytest.fixture
def set_env_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INFOBIP_API_KEY", "123")
    monkeypatch.setenv("INFOBIP_BASE_URL", "dummy.base.com")


@pytest.fixture
def mock_response(
    monkeypatch: pytest.MonkeyPatch, status_code: int, response_data: Dict[str, Any]
) -> None:
    def _mock_response(*args: Any, **kwargs: Any) -> DummyResponse:
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
def test_send_email(
    set_env_variables: Callable[[pytest.MonkeyPatch], None],
    mock_response: Callable[[pytest.MonkeyPatch, int, Dict[str, Any]], Any],
    status_code: int,
    response_data: Dict[str, Any],
    expected_exception: Optional[str],
) -> None:
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
