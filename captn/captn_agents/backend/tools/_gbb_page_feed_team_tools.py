from typing import Any, Dict

from ..toolboxes import Toolbox
from ._functions import (
    REPLY_TO_CLIENT_DESCRIPTION,
    ask_client_for_permission,
    ask_client_for_permission_description,
    reply_to_client,
)
from ._gbb_google_sheets_team_tools import (
    CHANGE_GOOGLE_ADS_ACCOUNT_DESCRIPTION,
    LIST_ACCESSIBLE_CUSTOMERS_WITH_ACCOUNT_TYPES_DESCRIPTION,
    LIST_SUB_ACCOUNTS_DESCRIPTION,
    GoogleSheetsTeamContext,
    list_accessible_customers_with_account_types,
    list_sub_accounts,
)
from ._google_ads_team_tools import (
    change_google_account,
)


def create_page_feed_team_toolbox(
    user_id: int,
    conv_id: int,
    kwargs: Dict[str, Any],
) -> Toolbox:
    toolbox = Toolbox()

    context = GoogleSheetsTeamContext(
        user_id=user_id,
        conv_id=conv_id,
        recommended_modifications_and_answer_list=kwargs[
            "recommended_modifications_and_answer_list"
        ],
        google_sheets_api_url=kwargs["google_sheets_api_url"],
        toolbox=toolbox,
    )
    toolbox.set_context(context)

    toolbox.add_function(REPLY_TO_CLIENT_DESCRIPTION)(reply_to_client)
    toolbox.add_function(
        description=ask_client_for_permission_description,
    )(ask_client_for_permission)
    toolbox.add_function(LIST_ACCESSIBLE_CUSTOMERS_WITH_ACCOUNT_TYPES_DESCRIPTION)(
        list_accessible_customers_with_account_types
    )
    toolbox.add_function(LIST_SUB_ACCOUNTS_DESCRIPTION)(list_sub_accounts)
    # toolbox.add_function(CREATE_GOOGLE_ADS_RESOURCES_DESCRIPTION)(
    #     create_google_ads_resources
    # )

    toolbox.add_function(
        description=CHANGE_GOOGLE_ADS_ACCOUNT_DESCRIPTION,
        name="change_google_ads_account_or_refresh_token",
    )(change_google_account)

    return toolbox
