import json
from datetime import datetime
from os import environ
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests

BASE_URL = environ.get("CAPTN_BACKEND_URL", "http://localhost:9000")
ALREADY_AUTHENTICATED = "User is already authenticated"


def get_login_url(user_id: int, conv_id: int) -> Dict[str, str]:
    params = {"user_id": user_id, "conv_id": conv_id}
    response = requests.get(f"{BASE_URL}/login", params=params, timeout=10)
    return response.json()  # type: ignore[no-any-return]


def list_accessible_customers(
    user_id: int, conv_id: int
) -> Union[List[str], Dict[str, str]]:
    login_url_response = get_login_url(user_id=user_id, conv_id=conv_id)
    if not login_url_response.get("login_url") == ALREADY_AUTHENTICATED:
        return login_url_response

    params = {"user_id": user_id}
    response = requests.get(
        f"{BASE_URL}/list-accessible-customers", params=params, timeout=10
    )
    if not response.ok:
        raise ValueError(response.content)
    # return ["8942812744", "2324127278", "7119828439", "6505006790", "8913146119"]
    return response.json()  # type: ignore[no-any-return]

    # return json.dumps(response.json())


def execute_query(
    user_id: int,
    conv_id: int,
    work_dir: str,
    customer_ids: Optional[List[str]] = None,
    query: Optional[str] = None,
) -> Union[str, Dict[str, str]]:
    login_url_response = get_login_url(user_id=user_id, conv_id=conv_id)
    if not login_url_response.get("login_url") == ALREADY_AUTHENTICATED:
        return login_url_response

    params: Dict[str, Any] = {
        "user_id": user_id,
    }
    if customer_ids:
        params["customer_ids"] = customer_ids
    if query:
        params["query"] = query

    response = requests.get(f"{BASE_URL}/search", params=params, timeout=10)
    if not response.ok:
        raise ValueError(response.content)

    response_json = response.json()

    file_name = "query_" + datetime.now().isoformat() + ".json"
    path = Path(work_dir) / file_name

    if not response_json:
        return "The query resulted with an empty response."

    with open(path, "w") as f:
        json.dump(response_json, f)

    return f"The result of the query saved at: {file_name}"


def _validate_input(customer_id: str, ad_group_id: str, ad_id: str) -> str:
    return_value = ""
    if not customer_id:
        return_value += "Parameter customer_id can NOT be empty.\n"
    if not ad_group_id:
        return_value += "Parameter ad_group_id can NOT be empty.\n"
    if not ad_id:
        return_value += "Parameter ad_id can NOT be empty.\n"
    return return_value

def pause_ad(user_id: int, conv_id: int, customer_id: str, ad_group_id: str, ad_id: str) -> str:
    validate_input_response = _validate_input(customer_id=customer_id, ad_group_id=ad_group_id, ad_id=ad_id)
    if validate_input_response:
        return validate_input_response

    login_url_response = get_login_url(user_id=user_id, conv_id=conv_id)
    if not login_url_response.get("login_url") == ALREADY_AUTHENTICATED:
        return login_url_response

    params: Dict[str, Any] = {
        "user_id": user_id,
        "customer_id": customer_id,
        "ad_group_id": ad_group_id,
        "ad_id": ad_id,
    }

    response = requests.get(f"{BASE_URL}/pause-ad", params=params, timeout=10)
    if not response.ok:
        raise ValueError(response.content)

    return response.json() # type: ignore[no-any-return]