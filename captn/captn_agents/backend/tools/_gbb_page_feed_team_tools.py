from dataclasses import dataclass
from typing import Annotated, Any, Dict, Optional

import pandas as pd

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
    GoogleSheetValues,
    # list_accessible_customers_with_account_types,
    # list_sub_accounts,
    get_sheet_data,
)
from ._google_ads_team_tools import (
    change_google_account,
)

VALIDATE_PAGE_FEED_DATA_DESCRIPTION = "Validate page feed data."


def _get_sheet_data_and_return_df(
    user_id: int,
    base_url: str,
    spreadsheet_id: str,
    title: str,
) -> pd.DataFrame:
    data = get_sheet_data(
        user_id=user_id,
        base_url=base_url,
        spreadsheet_id=spreadsheet_id,
        title=title,
    )
    values = GoogleSheetValues(**data)
    return pd.DataFrame(
        values.values[1:],
        columns=values.values[0],
    )


def _get_relevant_page_feeds_and_accounts(
    page_feeds_and_accounts_templ_df: pd.DataFrame,
    page_feeds_df: pd.DataFrame,
) -> pd.DataFrame:
    custom_labels = page_feeds_df["Custom Label"].unique()

    filtered_page_feeds_and_accounts_templ_df = pd.DataFrame(
        columns=page_feeds_and_accounts_templ_df.columns
    )
    # Get all columns that start with "Custom Label"
    custom_label_columns = [
        col
        for col in page_feeds_and_accounts_templ_df.columns
        if col.startswith("Custom Label")
    ]

    # Keep only rows that have at least one custom label in the custom_label_columns
    for row in page_feeds_and_accounts_templ_df.iterrows():
        row_custom_labels = row[1][custom_label_columns].values
        if any(
            row_custom_label in custom_labels for row_custom_label in row_custom_labels
        ):
            filtered_page_feeds_and_accounts_templ_df = pd.concat(
                [filtered_page_feeds_and_accounts_templ_df, row[1].to_frame().T],
                ignore_index=True,
            )

    return filtered_page_feeds_and_accounts_templ_df


@dataclass
class PageFeedTeamContext(GoogleSheetsTeamContext):
    page_feeds_and_accounts_templ_df: Optional[pd.DataFrame] = None
    page_feeds_df: Optional[pd.DataFrame] = None


def validate_page_feed_data(
    template_spreadsheet_id: Annotated[str, "Template spreadsheet id"],
    page_feed_spreadsheet_id: Annotated[str, "Page feed spreadsheet id"],
    page_feed_sheet_title: Annotated[
        str, "Page feed sheet title (within the page feed spreadsheet)"
    ],
    context: PageFeedTeamContext,
) -> str:
    account_templ_df = _get_sheet_data_and_return_df(
        user_id=context.user_id,
        base_url=context.google_sheets_api_url,
        spreadsheet_id=template_spreadsheet_id,
        title="Accounts",
    )
    for col in ["Manager Customer Id", "Customer Id"]:
        account_templ_df[col] = account_templ_df[col].str.replace("-", "")

    page_feeds_template_df = _get_sheet_data_and_return_df(
        user_id=context.user_id,
        base_url=context.google_sheets_api_url,
        spreadsheet_id=template_spreadsheet_id,
        title="Page Feeds",
    )
    page_feeds_template_df["Customer Id"] = page_feeds_template_df[
        "Customer Id"
    ].str.replace("-", "")
    # For columns 'Name' rename to 'Page Feed Name' or 'Account Name'
    page_feeds_and_accounts_templ_df = pd.merge(
        page_feeds_template_df,
        account_templ_df,
        on="Customer Id",
        how="left",
        suffixes=(" Page Feed", " Account"),
    )

    page_feeds_df = _get_sheet_data_and_return_df(
        user_id=context.user_id,
        base_url=context.google_sheets_api_url,
        spreadsheet_id=page_feed_spreadsheet_id,
        title=page_feed_sheet_title,
    )

    page_feeds_and_accounts_templ_df = _get_relevant_page_feeds_and_accounts(
        page_feeds_and_accounts_templ_df, page_feeds_df
    )

    if page_feeds_and_accounts_templ_df.empty:
        return "Page Feeds Templates don't have any matching Custom Labels with the newly provided Page Feeds data."

    context.page_feeds_and_accounts_templ_df = page_feeds_and_accounts_templ_df
    context.page_feeds_df = page_feeds_df
    avaliable_customers = page_feeds_and_accounts_templ_df[
        ["Manager Customer Id", "Customer Id", "Name Account"]
    ].drop_duplicates()
    avaliable_customers.rename(
        columns={"Manager Customer Id": "Login Customer Id"}, inplace=True
    )

    avaliable_customers_dict = avaliable_customers.set_index("Customer Id").to_dict(
        orient="index"
    )

    return f"""Data has been retrieved from Google Sheets.
Continue the process with the following customers:
{avaliable_customers_dict}
"""


UPDATE_PAGE_FEED_DESCRIPTION = "Update Google Ads Page Feeds."


def update_page_feeds(
    customer_id: Annotated[str, "Customer Id to update"],
    login_customer_id: Annotated[str, "Login Customer Id (Manager Account)"],
    context: PageFeedTeamContext,
) -> str:
    if context.page_feeds_and_accounts_templ_df is None:
        return f"Please validate the page feed data first by running the '{validate_page_feed_data.__name__}' function."
    return "All page feeds have been updated."


def create_page_feed_team_toolbox(
    user_id: int,
    conv_id: int,
    kwargs: Dict[str, Any],
) -> Toolbox:
    toolbox = Toolbox()

    context = PageFeedTeamContext(
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
