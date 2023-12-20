import json
from datetime import datetime
from os import environ
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from pydantic import BaseModel

BASE_URL = environ.get("CAPTN_BACKEND_URL", "http://localhost:9000")
ALREADY_AUTHENTICATED = "User is already authenticated"


def get_google_ads_team_capability() -> str:
    prefix = "Your capabilities are centered around Google Ads campaigns and include:\n"
    capabilities = [
        "Accessing detailed information about campaigns, ad groups, ads, and keywords.",
        "Modifying the status (ENABLED/PAUSED) of campaigns, ad groups, and ads.",
        "Creating new keywords for existing campaigns",
        "Removing campaigns/ ad groups / ads / positive and negative keywords",
    ]

    return prefix + "- " + "\n- ".join(capabilities)


def get_login_url(user_id: int, conv_id: int) -> Dict[str, str]:
    params = {"user_id": user_id, "conv_id": conv_id}
    response = requests.get(f"{BASE_URL}/login", params=params, timeout=60)
    retval: Dict[str, str] = response.json()
    return retval  # type: ignore[no-any-return]


def list_accessible_customers(
    user_id: int, conv_id: int
) -> Union[List[str], Dict[str, str]]:
    login_url_response = get_login_url(user_id=user_id, conv_id=conv_id)
    if not login_url_response.get("login_url") == ALREADY_AUTHENTICATED:
        return login_url_response

    params = {"user_id": user_id}
    response = requests.get(
        f"{BASE_URL}/list-accessible-customers", params=params, timeout=60
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

    response = requests.get(f"{BASE_URL}/search", params=params, timeout=60)
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


def google_ads_create_update(
    user_id: int,
    conv_id: int,
    clients_approval_message: str,
    ad: BaseModel,
    endpoint: str = "/update-ad",
) -> Union[Dict[str, Any], str]:
    if not clients_approval_message:
        return "You must aks the client for the permission first!!!"

    login_url_response = get_login_url(user_id=user_id, conv_id=conv_id)
    if not login_url_response.get("login_url") == ALREADY_AUTHENTICATED:
        return login_url_response

    params: Dict[str, Any] = ad.model_dump()
    params["user_id"] = user_id

    response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=60)
    if not response.ok:
        raise ValueError(response.content)

    response_dict: Dict[str, Any] = response.json()  # type: ignore[no-any-return]
    return response_dict
