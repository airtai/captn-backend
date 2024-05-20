import json
from os import environ
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel
from requests import get as requests_get

BASE_URL = environ.get("CAPTN_BACKEND_URL", "http://localhost:9000")
ALREADY_AUTHENTICATED = "User is already authenticated"

__all__ = (
    "get_google_ads_team_capability",
    "get_login_url",
    "list_accessible_customers",
    "execute_query",
    "get_user_ids_and_emails",
    "google_ads_create_update",
)


def get_google_ads_team_capability() -> str:
    prefix = "Your capabilities are centered around Google Ads campaigns and include:\n"
    capabilities = [
        "Accessing detailed information about campaigns, ad groups, ads, and keywords.",
        "Modifying the status (ENABLED/PAUSED) of campaigns, ad groups, and ads.",
        "Creating new keywords for existing campaigns.",
        "Removing campaigns/ ad groups / ads / positive and negative keywords.",
        "Updating Ad Copies.",
        "Adding/removing location targeting",
    ]

    return prefix + "- " + "\n- ".join(capabilities)


def get_login_url(
    user_id: int, conv_id: int, force_new_login: bool = False
) -> Dict[str, str]:
    params = {
        "user_id": user_id,
        "conv_id": conv_id,
        "force_new_login": force_new_login,
    }
    response = requests_get(f"{BASE_URL}/login", params=params, timeout=60)
    retval: Dict[str, str] = response.json()
    return retval


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
    response = requests_get(
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
ACCOUNT_NOT_ACTIVATED = (
    "be accessed because it is not yet enabled or has been deactivated"
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

    response = requests_get(f"{BASE_URL}/search", params=params, timeout=60)
    if not response.ok:
        if AUTHENTICATION_ERROR in response.text:
            content = AUTHENTICATION_ERROR
        else:
            content = clean_error_response(response.content)
            if ACCOUNT_NOT_ACTIVATED in content:
                content = f"""We have received the following error from Google Ads API:

{content}

If you have just created the account, please wait for a few hours before trying again.
If the account has been active for a while, please check the account status in the Google Ads UI.
"""
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
    response = requests_get(f"{BASE_URL}/get-user-ids-and-emails", timeout=60)
    if not response.ok:
        raise ValueError(response.content)
    return response.json()  # type: ignore[no-any-return]


NOT_IN_QUESTION_ANSWER_LIST = """You must ask the client for the permission first by using the 'ask_client_for_permission' function by using the same JSON for the 'modification_function_parameters' parameter.
If you don't use the SAME JSON for the 'modification_function_parameters' parameter, the modification will NOT be approved!
So before calling the current function again, you MUST call the 'ask_client_for_permission' function with the same JSON for the 'modification_function_parameters' parameter.

"modification_function_parameters": """
NOT_APPROVED = (
    "The client did not approve the modification. The client must approve the modification by answering 'Yes' the message sent by the 'ask_client_for_permission' function!"
    "If the message was sent by the 'reply_to_client' function, the modification will NOT be approved!"
    "If the answer is 'Yes ...', the modification will NOT be approved - the answer must be 'Yes' and nothing else."
    "Please send a new message to the client (by using 'ask_client_for_permission') and ask for the permission again and tell him that only for answer 'Yes' the modification will be done."
)


FIELDS_ARE_NOT_MENTIONED_ERROR_MSG = (
    "The client must be informed about ALL the changes that are going to be made!"
    "If you have already asked client for the permission regarding the changes, you MUST apologize to him and ask for the permission again by using the 'ask_client_for_permission' but this time you must include all the changes that are going to be made (mentioned below)."
    "e.g. 'We apologize for bothering you again. I have made a mistake and I forgot to mention some of the changes that are going to be made. I have to ask you again for the permission. The changes that are going to be made are the following: ...'"
    "The following fields were NOT mentioned in the approval question for the client. Please inform the client about the modifications of the following fields (use the EXACT names as the ones listed below e.g. if a field is called 'super_cool_field', you MUST reference it as 'super_cool_field'!):\n"
)

IGNORE_FIELDS = [
    "update_existing_headline_index",
    "update_existing_description_index",
    "resource_type",
    "location_ids",
    "network_settings_target_google_search",
    "network_settings_target_search_network",
    "network_settings_target_content_network",
]
FIELD_MAPPING = {
    "keyword_text": "keyword",
    "keyword_match_type": "match_type",
}


def clean_nones(value: Any) -> Any:
    """
    Recursively remove all None values from dictionaries and lists, and returns
    the result as a new dictionary or list.
    """
    if isinstance(value, list):
        return [clean_nones(x) for x in value if x is not None]
    elif isinstance(value, dict):
        return {key: clean_nones(val) for key, val in value.items() if val is not None}
    else:
        return value


def check_for_client_approval(
    modification_function_parameters: Dict[str, Any],
    recommended_modifications_and_answer_list: List[
        Tuple[Dict[str, Any], Optional[str]]
    ],
) -> Optional[str]:
    modification_function_parameters = clean_nones(modification_function_parameters)

    clients_question_list = [x[0] for x in recommended_modifications_and_answer_list]

    if modification_function_parameters not in clients_question_list:
        error_msg = NOT_IN_QUESTION_ANSWER_LIST + json.dumps(
            modification_function_parameters, indent=2
        )
        return error_msg

    for client_question, client_answer in recommended_modifications_and_answer_list:
        if (
            client_question == modification_function_parameters
            and client_answer is not None
            and client_answer.strip().lower() == "yes"
        ):
            return None

    return NOT_APPROVED


def google_ads_create_update(
    user_id: int,
    conv_id: int,
    ad: BaseModel,
    recommended_modifications_and_answer_list: List[
        Tuple[Dict[str, Any], Optional[str]]
    ],
    endpoint: str = "/update-ad-group-ad",
    already_checked_clients_approval: bool = False,
) -> Union[Dict[str, Any], str]:
    if not already_checked_clients_approval:
        error_msg = check_for_client_approval(
            modification_function_parameters=ad.model_dump(),
            recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
        )
        if error_msg:
            raise ValueError(error_msg)

    login_url_response = get_login_url(user_id=user_id, conv_id=conv_id)
    if not login_url_response.get("login_url") == ALREADY_AUTHENTICATED:
        return login_url_response

    params: Dict[str, Any] = ad.model_dump()
    params["user_id"] = user_id

    response = requests_get(f"{BASE_URL}{endpoint}", params=params, timeout=60)
    if not response.ok:
        raise ValueError(response.content)

    response_dict: Union[Dict[str, Any], str] = response.json()
    return response_dict
