from typing import Annotated, Any, Dict, List

from ..toolboxes import Toolbox
from ._functions import (
    REPLY_TO_CLIENT_DESCRIPTION,
    ask_client_for_permission,
    ask_client_for_permission_description,
    reply_to_client,
)
from ._gbb_google_sheets_team_tools import (
    CHANGE_GOOGLE_ADS_ACCOUNT_DESCRIPTION,
    # LIST_ACCESSIBLE_CUSTOMERS_WITH_ACCOUNT_TYPES_DESCRIPTION,
    # LIST_SUB_ACCOUNTS_DESCRIPTION,
    GoogleSheetsTeamContext,
    # list_accessible_customers_with_account_types,
    # list_sub_accounts,
    get_sheet_data,
)
from ._google_ads_team_tools import (
    change_google_account,
)

VALIDATE_PAGE_FEED_DATA_DESCRIPTION = "Validate page feed data."


def validate_page_feed_data(
    template_spreadsheet_id: Annotated[str, "Template spreadsheet id"],
    page_feed_spreadsheet_id: Annotated[str, "Page feed spreadsheet id"],
    page_feed_sheet_title: Annotated[
        str, "Page feed sheet title (within the page feed spreadsheet)"
    ],
    context: GoogleSheetsTeamContext,
) -> str:
    account_data_dict = get_sheet_data(
        user_id=context.user_id,
        base_url=context.google_sheets_api_url,
        spreadsheet_id=template_spreadsheet_id,
        title="Accounts",
    )
    print(account_data_dict)
    return "Data has been retrieved from Google Sheets. Continue with the process."


UPDATE_PAGE_FEED_DESCRIPTION = "Update Google Ads Page Feeds."


def update_page_feeds(
    customer_ids_to_update: Annotated[List[str], "List of customer ids to update"],
    context: GoogleSheetsTeamContext,
) -> str:
    return "All page feeds have been updated."


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
    # toolbox.add_function(LIST_ACCESSIBLE_CUSTOMERS_WITH_ACCOUNT_TYPES_DESCRIPTION)(
    #     list_accessible_customers_with_account_types
    # )
    # toolbox.add_function(LIST_SUB_ACCOUNTS_DESCRIPTION)(list_sub_accounts)
    toolbox.add_function(VALIDATE_PAGE_FEED_DATA_DESCRIPTION)(validate_page_feed_data)
    toolbox.add_function(UPDATE_PAGE_FEED_DESCRIPTION)(update_page_feeds)

    toolbox.add_function(
        description=CHANGE_GOOGLE_ADS_ACCOUNT_DESCRIPTION,
        name="change_google_ads_account_or_refresh_token",
    )(change_google_account)

    return toolbox
