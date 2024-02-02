from os import environ
from typing import Any, Dict

import requests

INFOBIP_API_KEY = environ["INFOBIP_API_KEY"]
INFOBIP_BASE_URL = environ["INFOBIP_BASE_URL"]


# ToDo: Create support@captn.ai and add to infobip portal
def send_email(
    *, from_email: str = "info@airt.ai", to_email: str, subject: str, body_text: str
) -> Dict[str, Any]:
    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Accept": "application/json",
    }

    files = {
        "from": (None, from_email),
        "subject": (None, subject),
        "to": (None, to_email),
        "html": (None, body_text),
    }

    response = requests.post(
        f"https://{INFOBIP_BASE_URL}/email/3/send",
        headers=headers,
        files=files,
        timeout=5,
    )

    resp_json: Dict[str, Any] = response.json()

    if not response.ok:
        raise Exception(f"Failed to send email: {response.status_code}, {resp_json}")

    return resp_json


if __name__ == "__main__":
    r = send_email(
        from_email="info@airt.ai",
        to_email="kumaran@airt.ai",
        subject="Hi there!",
        body_text="It is me, SDK! <br> <b>How are you?</b>",
    )
    print(r)
