from os import environ
from typing import Any, Dict, Optional

import requests

INFOBIP_API_KEY = environ["INFOBIP_API_KEY"]
INFOBIP_BASE_URL = environ["INFOBIP_BASE_URL"]


def send_email(
    *,
    from_email: Optional[str] = None,
    to_email: str,
    subject: str,
    body_text: str,
) -> Dict[str, Any]:
    if from_email is None:
        domain = environ.get("DOMAIN", None)

        if domain is None:
            from_email = f"Capt’n.ai Staging Support <support-staging@{domain}>"
        else:
            if "staging" in domain or "localhost" in domain or "127.0.0.1" in domain:
                from_email = f"Capt’n.ai Staging Support <support-staging@{domain}>"
            else:
                from_email = f"Capt’n.ai Support <support@{domain}>"

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
