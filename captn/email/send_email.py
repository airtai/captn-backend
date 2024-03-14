from os import environ
from typing import Any, Dict, Optional

import requests


def send_email(
    *,
    from_email: Optional[str] = None,
    to_email: str,
    subject: str,
    body_text: str,
) -> Dict[str, Any]:
    INFOBIP_API_KEY = environ.get("INFOBIP_API_KEY", None)
    INFOBIP_BASE_URL = environ.get("INFOBIP_BASE_URL", None)

    if INFOBIP_API_KEY is None or INFOBIP_BASE_URL is None:
        raise Exception(
            "INFOBIP_API_KEY and INFOBIP_BASE_URL environment variables are required."
        )

    if from_email is None:
        domain = environ.get("DOMAIN", None)

        if domain is None:
            from_email = "Capt’n.ai Staging Support <support-staging@captn.ai>"
        else:
            if "staging" in domain or "localhost" in domain or "127.0.0.1" in domain:
                from_email = "Capt’n.ai Staging Support <support-staging@captn.ai>"
            else:
                from_email = "Capt’n.ai Support <support@captn.ai>"

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
        # from_email="support@captn.ai",
        to_email="kumaran@airt.ai",
        subject="Hi there!",
        body_text="It is me, SDK! <br> <b>How are you?</b>",
    )
    print(r)
