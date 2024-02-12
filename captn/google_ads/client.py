import json
from os import environ
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
        "Creating new keywords for existing campaigns.",
        "Removing campaigns/ ad groups / ads / positive and negative keywords.",
        "Updating Ad Copies.",
    ]

    return prefix + "- " + "\n- ".join(capabilities)


def get_login_url(user_id: int, conv_id: int) -> Dict[str, str]:
    params = {"user_id": user_id, "conv_id": conv_id}
    response = requests.get(f"{BASE_URL}/login", params=params, timeout=60)
    retval: Dict[str, str] = response.json()
    return retval  # type: ignore[no-any-return]


def list_accessible_customers(
    user_id: int, conv_id: int, get_only_non_manager_accounts: bool = False
) -> Union[List[str], Dict[str, str]]:
    login_url_response = get_login_url(user_id=user_id, conv_id=conv_id)
    if not login_url_response.get("login_url") == ALREADY_AUTHENTICATED:
        return login_url_response

    params = {
        "user_id": user_id,
        "get_only_non_manager_accounts": get_only_non_manager_accounts,
    }
    response = requests.get(
        f"{BASE_URL}/list-accessible-customers", params=params, timeout=60
    )
    if not response.ok:
        raise ValueError(response.content)
    # return ["8942812744", "2324127278", "7119828439", "6505006790", "8913146119"]

    respone_json = response.json()
    return respone_json  # type: ignore[no-any-return]


def clean_error_response(content: bytes) -> str:
    content_str = str(content, "utf-8")

    detail = json.loads(content_str)["detail"]
    detail_list = detail.split("\n")

    return "\n".join(
        [row for row in detail_list if "message" in row and "created_time" not in row]
    )


def execute_query(
    user_id: int,
    conv_id: int,
    work_dir: Optional[str] = None,
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
        content = clean_error_response(response.content)
        raise ValueError(content)

    response_json = response.json()

    if not response_json:
        return "The query resulted with an empty response."

    # file_name = "query_" + datetime.now().isoformat() + ".json"
    # path = Path(work_dir) / file_name
    # with open(path, "w") as f:
    #     json.dump(response_json, f)

    # return f"The result of the query saved at: {file_name}"
    return str(response_json)


def get_user_ids_and_emails() -> str:
    response = requests.get(f"{BASE_URL}/get-user-ids-and-emails", timeout=60)
    if not response.ok:
        raise ValueError(response.content)
    return response.json()  # type: ignore[no-any-return]


def google_ads_create_update(
    user_id: int,
    conv_id: int,
    clients_approval_message: str,
    client_approved_modicifation_for_this_resource: bool,
    ad: BaseModel,
    endpoint: str = "/update-ad-group-ad",
) -> Union[Dict[str, Any], str]:
    if (
        not clients_approval_message
        or not client_approved_modicifation_for_this_resource
    ):
        return "You must inform the client about all the parameters which will be used and ask for the permission first!!!"

    login_url_response = get_login_url(user_id=user_id, conv_id=conv_id)
    if not login_url_response.get("login_url") == ALREADY_AUTHENTICATED:
        return login_url_response

    params: Dict[str, Any] = ad.model_dump()
    params["user_id"] = user_id

    response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=60)
    if not response.ok:
        raise ValueError(response.content)

    response_dict: Union[Dict[str, Any], str] = response.json()
    return response_dict
