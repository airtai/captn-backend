from os import environ

from infobip_channels.email.channel import EmailChannel

INFOBIP_API_KEY = environ.get("INFOBIP_API_KEY")
INFOBIP_BASE_URL = environ.get("INFOBIP_BASE_URL")


def send_email(
    *, from_email: str = "info@airt.ai", to_email: str, subject: str, body: str
) -> None:
    channel = EmailChannel.from_auth_params(
        {"base_url": INFOBIP_BASE_URL, "api_key": INFOBIP_API_KEY}
    )

    email_response = channel.send_email_message(
        {"from": from_email, "to": to_email, "subject": subject, "text": body}
    )

    print(email_response)

    if not email_response.status_code.value == 200:
        raise ValueError(email_response)
