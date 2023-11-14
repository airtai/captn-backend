from os import environ
from typing import Any, Dict, List, Optional

BASE_URL = environ.get(
    "BASE_URL", "https://captn-ads-auth.westeurope.cloudapp.azure.com"
)


def get_login_url(user_id: int) -> Dict[str, str]:
    return {
        "login_url": f"https://accounts.google.com/o/oauth2/auth?client_id=476761633153-o81jdsampd62i4biqef0k82494mepkjs.apps.googleusercontent.com&redirect_uri=http://localhost:9000/login/callback&response_type=code&scope=https://www.googleapis.com/auth/adwords email&access_type=offline&prompt=consent&state={user_id}"
    }


def list_accessible_customers(user_id: int) -> List[str]:
    return ["8942812744", "2324127278", "7119828439", "6505006790", "8913146119"]


def execute_query(
    user_id: int, customer_ids: Optional[List[str]] = None, query: Optional[str] = None
) -> Dict[str, Optional[List[Dict[str, Any]]]]:
    if customer_ids is None:
        customer_ids = ["all"]
    if not query:
        query = (
            "SELECT campaign.id, campaign.name, ad_group.id, ad_group.name "
            "FROM keyword_view WHERE segments.date DURING LAST_7_DAYS"
        )
    return {
        "8942812744": [],
        "2324127278": [
            {
                "campaign": {
                    "resourceName": "customers/2324127278/campaigns/20761810762",
                    "name": "Website traffic-Search-3",
                    "id": "20761810762",
                },
                "adGroup": {
                    "resourceName": "customers/2324127278/adGroups/156261983518",
                    "id": "156261983518",
                    "name": "Ad group 1",
                },
                "keywordView": {
                    "resourceName": "customers/2324127278/keywordViews/156261983518~304689274443"
                },
            },
            {
                "campaign": {
                    "resourceName": "customers/2324127278/campaigns/20761810762",
                    "name": "Website traffic-Search-3",
                    "id": "20761810762",
                },
                "adGroup": {
                    "resourceName": "customers/2324127278/adGroups/156261983518",
                    "id": "156261983518",
                    "name": "Ad group 1",
                },
                "keywordView": {
                    "resourceName": "customers/2324127278/keywordViews/156261983518~327558728813"
                },
            },
            {
                "campaign": {
                    "resourceName": "customers/2324127278/campaigns/20761810762",
                    "name": "Website traffic-Search-3",
                    "id": "20761810762",
                },
                "adGroup": {
                    "resourceName": "customers/2324127278/adGroups/156261983518",
                    "id": "156261983518",
                    "name": "Ad group 1",
                },
                "keywordView": {
                    "resourceName": "customers/2324127278/keywordViews/156261983518~327982491964"
                },
            },
            {
                "campaign": {
                    "resourceName": "customers/2324127278/campaigns/20761810762",
                    "name": "Website traffic-Search-3",
                    "id": "20761810762",
                },
                "adGroup": {
                    "resourceName": "customers/2324127278/adGroups/156261983518",
                    "id": "156261983518",
                    "name": "Ad group 1",
                },
                "keywordView": {
                    "resourceName": "customers/2324127278/keywordViews/156261983518~352068863258"
                },
            },
        ],
    }
