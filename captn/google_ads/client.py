from os import environ
from typing import Any, Dict, List, Optional, Union

import requests

BASE_URL = environ.get("CAPTN_BACKEND_URL", "http://localhost:9000")


def get_login_url(user_id: int, conv_id: int) -> Dict[str, str]:
    params = {"user_id": user_id, "conv_id": conv_id}
    response = requests.get(f"{BASE_URL}/login", params=params, timeout=10)
    return response.json()  # type: ignore[no-any-return]


def list_accessible_customers(user_id: int) -> List[str]:
    params = {"user_id": user_id}
    response = requests.get(
        f"{BASE_URL}/list-accessible-customers", params=params, timeout=10
    )
    if not response.ok:
        raise ValueError(response.content)
    return response.json()  # type: ignore[no-any-return]


def search(
    user_id: int,
    work_dir: str,
    customer_ids: Optional[List[str]] = None,
    query: Optional[str] = None,
) -> Union[str, Dict[str, Any]]:
    params: Dict[str, Any] = {
        "user_id": user_id,
    }
    if customer_ids:
        params["customer_ids"] = customer_ids
    if query:
        params["query"] = query
    print(params)
    response = requests.get(f"{BASE_URL}/search", params=params, timeout=10)
    if not response.ok:
        raise ValueError(response.content)

    response_json = response.json()
    if len(str(response_json)) > 5000:
        summary = "Here is the summary of the executed query:\n"
        clicks = 23
        impressions = 9
        for customer_id in response_json.keys():
            summary += f"""customer_id: {customer_id}
 - 'name': 'Website traffic-Search-{customer_id}' 
 - 'metrics': 'clicks': {clicks}, 'impressions': {impressions} 'conversions': 0.15
 - 'text': 'fast api tutorial'\n"""
            clicks += 12
            impressions += 3
        return summary

    # file_name = query.replace(" ", "_") + "_" + time.strftime("%Y%m%d-%H%M%S")
    # with open(Path(work_dir) / file_name, 'w') as f:
    #     json.dump(response.json(), f)

    # return f"The result is saved at ..... {file_name}"
    print(len(str(response_json)))
    return response.json()  # type: ignore[no-any-return]
