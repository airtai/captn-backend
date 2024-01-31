import pytest
from infobip_channels.core.models import ResponseStatus
from infobip_channels.email.channel import EmailChannel
from infobip_channels.email.models.response.send_email import (
    SendEmailResponse,
    SendEmailResponseMessage,
)
from requests.models import Response


def test_send_email(monkeypatch):
    monkeypatch.setenv("INFOBIP_API_KEY", "123")
    monkeypatch.setenv("INFOBIP_BASE_URL", "dummy.base.com")

    from openai_agent.send_email import send_email

    def mock_response(*args, **kwargs):
        response = Response()
        response.status_code = 200

        dummy_response_status = ResponseStatus(
            group_id=1,
            group_name="PENDING",
            id=26,
            name="PENDING_ACCEPTED",
            description="Message accepted, pending for delivery.",
            action=None,
        )
        email_response = SendEmailResponse(
            status_code=200,
            rawResponse=response,
            messages=[SendEmailResponseMessage(status=dummy_response_status)],
        )

        return email_response

    monkeypatch.setattr(EmailChannel, "send_email_message", mock_response)

    send_email(to_email="test@airt.ai", subject="Hi there!", body="It is me, SDK!")


def test_send_email_raise_exception(monkeypatch):
    monkeypatch.setenv("INFOBIP_API_KEY", "123")
    monkeypatch.setenv("INFOBIP_BASE_URL", "dummy.base.com")

    from openai_agent.send_email import send_email

    def mock_response(*args, **kwargs):
        response = Response()
        response.status_code = 500

        dummy_response_status = ResponseStatus(
            group_id=1,
            group_name="PENDING",
            id=26,
            name="PENDING_ACCEPTED",
            description="Message accepted, pending for delivery.",
            action=None,
        )
        email_response = SendEmailResponse(
            status_code=500,
            rawResponse=response,
            messages=[SendEmailResponseMessage(status=dummy_response_status)],
        )

        return email_response

    monkeypatch.setattr(EmailChannel, "send_email_message", mock_response)

    with pytest.raises(ValueError):
        send_email(to_email="test@airt.ai", subject="Hi there!", body="It is me, SDK!")
