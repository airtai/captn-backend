import json
from os import environ
from typing import Any, Dict, List, Optional, Tuple, Union

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


AUTHENTICATION_ERROR = "Please try to execute the command again."


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
        if AUTHENTICATION_ERROR in response.text:
            content = AUTHENTICATION_ERROR
        else:
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


NOT_IN_QUESTION_ANSWER_LIST = (
    "You must ask the client for the permission first by using the 'ask_client_for_permission' function."
    "If you have already asked the client for the permission, make sure that the 'proposed_changes' parameter you have used in the 'ask_client_for_permission' function is the same as the 'modification_question' you are currently using (EVERY character must be the same)."
)
NOT_APPROVED = (
    "The client did not approve the modification. The client must approve the modification by answering 'Yes' to the question."
    "If the answer is 'Yes ...', the modification will NOT be approved - the answer must be 'Yes' and nothing else."
    "Please send a new message to the client (by using 'ask_client_for_permission') and ask for the permission again and tell him that only for answer 'Yes' the modification will be done."
)


def _check_for_client_approval(
    modification_question: str,
    clients_approval_message: str,
    clients_question_answere_list: List[Tuple[str, Optional[str]]],
) -> bool:
    if (
        modification_question,
        clients_approval_message,
    ) not in clients_question_answere_list:
        raise ValueError(NOT_IN_QUESTION_ANSWER_LIST)
    if clients_approval_message.lower().strip() != "yes":
        raise ValueError(NOT_APPROVED)

    return True


def google_ads_create_update(
    user_id: int,
    conv_id: int,
    clients_approval_message: str,
    modification_question: str,
    ad: BaseModel,
    clients_question_answere_list: List[Tuple[str, Optional[str]]],
    endpoint: str = "/update-ad-group-ad",
) -> Union[Dict[str, Any], str]:
    _check_for_client_approval(
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        clients_question_answere_list=clients_question_answere_list,
    )
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
