import http.client
import json
from codecs import encode
from os import environ
from typing import Any, Dict

INFOBIP_API_KEY = environ["INFOBIP_API_KEY"]
INFOBIP_BASE_URL = environ["INFOBIP_BASE_URL"]


# ToDo: Create support@captn.ai and add to infobip portal
def send_email(
    *, from_email: str = "harish@airt.ai", to_email: str, subject: str, body_text: str
) -> Dict[str, Any]:
    conn = http.client.HTTPSConnection(  # nosemgrep: python.lang.security.audit.httpsconnection-detected.httpsconnection-detected
        INFOBIP_BASE_URL
    )
    dataList = []
    boundary = "wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T"
    dataList.append(encode("--" + boundary))
    dataList.append(encode("Content-Disposition: form-data; name=from;"))

    dataList.append(encode("Content-Type: {}".format("text/plain")))
    dataList.append(encode(""))

    dataList.append(encode(from_email))
    dataList.append(encode("--" + boundary))
    dataList.append(encode("Content-Disposition: form-data; name=subject;"))

    dataList.append(encode("Content-Type: {}".format("text/plain")))
    dataList.append(encode(""))

    dataList.append(encode(subject))
    dataList.append(encode("--" + boundary))
    dataList.append(encode("Content-Disposition: form-data; name=to;"))

    dataList.append(encode("Content-Type: {}".format("text/plain")))
    dataList.append(encode(""))

    dataList.append(encode('{"to":"' + to_email + '"}'))
    dataList.append(encode("--" + boundary))
    dataList.append(encode("Content-Disposition: form-data; name=text;"))

    dataList.append(encode("Content-Type: {}".format("text/plain")))
    dataList.append(encode(""))

    dataList.append(encode(body_text))
    dataList.append(encode("--" + boundary + "--"))
    dataList.append(encode(""))
    body = b"\r\n".join(dataList)
    payload = body
    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Accept": "application/json",
        "Content-type": f"multipart/form-data; boundary={boundary}",
    }

    conn.request("POST", "/email/3/send", payload, headers)
    res = conn.getresponse()

    data = res.read()
    decoded: Dict[str, Any] = json.loads(data.decode("utf-8"))

    if res.status != 200:
        raise Exception(f"Failed to send email: {res.status}, {decoded}")

    return decoded


if __name__ == "__main__":
    r = send_email(
        from_email="harish@airt.ai",
        to_email="kumaran@airt.ai",
        subject="Hi there!",
        body_text="It is me, SDK!",
    )
    print(r)
