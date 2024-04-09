from typing import Dict, List, Optional, Union

from typing_extensions import Annotated

from ....google_ads.client import execute_query as execute_query_client
from ....google_ads.client import get_login_url
from ....google_ads.client import (
    list_accessible_customers as list_accessible_customers_client,
)
from ._functions import Context

__all__ = (
    "change_google_account",
    "change_google_account_description",
    "execute_query",
    "execute_query_description",
    "list_accessible_customers",
    "list_accessible_customers_description",
)

change_google_account_description = "This method should be used only when the client explicitly asks for the change of the Google account (the account which will be used for Google Ads)!"


def change_google_account(context: Context) -> Dict[str, str]:
    user_id = context.user_id
    conv_id = context.conv_id

    return get_login_url(user_id=user_id, conv_id=conv_id, force_new_login=True)


list_accessible_customers_description = "List all the customers accessible to the user"


def list_accessible_customers(context: Context) -> Union[List[str], Dict[str, str]]:
    user_id = context.user_id
    conv_id = context.conv_id

    return list_accessible_customers_client(user_id=user_id, conv_id=conv_id)


execute_query_description = """Query the Google Ads API.
If not told differently, do NOT retrieve information about the REMOVED resources (campaigns, ad groups, ads...) i.e. use the 'WHERE' clause to filter out the REMOVED resources!"""

query_description = """Database query.
Unless told differently, do NOT retrieve information about the REMOVED resources (campaigns, ad groups, ads...)!
NEVER try to retrieve field "ad_group_ad.ad.strength" because field "strength" does NOT exist!"""


def execute_query(
    context: Context,
    customer_ids: Annotated[Optional[List[str]], "List of customer ids"] = None,
    query: Annotated[Optional[str], query_description] = None,
) -> Union[str, Dict[str, str]]:
    user_id = context.user_id
    conv_id = context.conv_id
    return execute_query_client(
        user_id=user_id, conv_id=conv_id, customer_ids=customer_ids, query=query
    )
