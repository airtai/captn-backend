from os import environ
from typing import Any, Dict, List, Optional

import requests

BASE_URL = environ.get("CAPTN_BACKEND_URL", "http://localhost:9000")


def get_login_url(user_id: int) -> Dict[str, str]:
    params = {"user_id": user_id}
    response = requests.get(f"{BASE_URL}/login", params=params)
    return response.json()


def list_accessible_customers(user_id: int) -> List[str]:
    params = {"user_id": user_id}
    response = requests.get(f"{BASE_URL}/list-accessible-customers", params=params)
    if not response.ok:
        raise ValueError(response.content)
    return response.json()


def search(
    user_id: int, customer_ids: Optional[List[str]] = None, query: Optional[str] = None
) -> Dict[str, Any]:
    params = {
        "user_id": user_id,
    }
    if customer_ids:
        params["customer_ids"] = customer_ids
    if query:
        params["query"] = query
    response = requests.get(f"{BASE_URL}/search", params=params)
    if not response.ok:
        raise ValueError(response.content)
    return response.json()
