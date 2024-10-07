import json
from dataclasses import dataclass
from typing import Annotated, Any, Dict, Optional

import pandas as pd

from google_ads.model import AddPageFeedItems, RemoveResource

from ....google_ads.client import (
    execute_query,
    google_ads_create_update,
    google_ads_post_or_get,
)
from ..toolboxes import Toolbox
from ._functions import (
    REPLY_TO_CLIENT_DESCRIPTION,
    ask_client_for_permission,
    ask_client_for_permission_description,
    reply_to_client,
)
from ._gbb_google_sheets_team_tools import (
    CHANGE_GOOGLE_ADS_ACCOUNT_DESCRIPTION,
    GoogleSheetsTeamContext,
    GoogleSheetValues,
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


def _get_page_feed_asset_sets(
    user_id: int,
    conv_id: int,
    customer_id: str,
    login_customer_id: str,
) -> Dict[str, Dict[str, str]]:
    page_feed_asset_sets: Dict[str, Dict[str, str]] = {}
    query = """SELECT
asset_set.id,
asset_set.name,
asset_set.resource_name
FROM campaign_asset_set
WHERE
campaign.advertising_channel_type = 'PERFORMANCE_MAX'
AND asset_set.type = 'PAGE_FEED'
AND asset_set.status = 'ENABLED'
AND campaign_asset_set.status = 'ENABLED'
AND campaign.status != 'REMOVED'
"""
    response = execute_query(
        user_id=user_id,
        conv_id=conv_id,
        customer_ids=[customer_id],
        login_customer_id=login_customer_id,
        query=query,
    )
    if isinstance(response, dict):
        raise ValueError(response)

    response_json = json.loads(response.replace("'", '"'))

    if customer_id not in response_json:
        return page_feed_asset_sets

    for row in response_json[customer_id]:
        asset_set = row["assetSet"]
        page_feed_asset_sets[asset_set["name"]] = {
            "id": asset_set["id"],
            "resourceName": asset_set["resourceName"],
        }

    return page_feed_asset_sets


def _get_page_feed_items(
    user_id: int,
    conv_id: int,
    customer_id: str,
    login_customer_id: str,
    asset_set_resource_name: str,
) -> pd.DataFrame:
    query = f"""
SELECT
  asset.id,
  asset.name,
  asset.type,
  asset.page_feed_asset.page_url,
  asset.page_feed_asset.labels
FROM
  asset_set_asset
WHERE
  asset.type = 'PAGE_FEED'
  AND asset_set_asset.asset_set = '{asset_set_resource_name}'
  AND asset_set_asset.status != 'REMOVED'
"""  # nosec: [B608]

    response = execute_query(
        user_id=user_id,
        conv_id=conv_id,
        customer_ids=[customer_id],
        login_customer_id=login_customer_id,
        query=query,
    )

    if isinstance(response, dict):
        raise ValueError(response)

    response_json = json.loads(response.replace("'", '"'))

    page_urls_and_labels_df = pd.DataFrame(columns=["Id", "Page URL", "Custom Label"])
    for asset in response_json[customer_id]:
        id = asset["asset"]["id"]
        url = asset["asset"]["pageFeedAsset"]["pageUrl"].strip()

        if "labels" in asset["asset"]["pageFeedAsset"]:
            labels_list = asset["asset"]["pageFeedAsset"]["labels"]
            labels = "; ".join(labels_list)
        else:
            labels = None
        page_urls_and_labels_df = pd.concat(
            [
                page_urls_and_labels_df,
                pd.DataFrame([{"Id": id, "Page URL": url, "Custom Label": labels}]),
            ],
            ignore_index=True,
        )

    return page_urls_and_labels_df


def _sync_page_feed_asset_set(
    user_id: int,
    conv_id: int,
    customer_id: str,
    login_customer_id: str,
    page_feeds_and_accounts_templ_df: pd.DataFrame,
    page_feeds_df: pd.DataFrame,
    page_feed_asset_set_name: str,
    page_feed_asset_set: Dict[str, str],
) -> str:
    page_feed_rows = page_feeds_and_accounts_templ_df[
        page_feeds_and_accounts_templ_df["Name Page Feed"] == page_feed_asset_set_name
    ]
    if page_feed_rows.empty:
        return f"Page feed '{page_feed_asset_set_name}' not found in the page feed template data.\n"

    elif page_feed_rows["Customer Id"].nunique() > 1:
        return f"Page feed template has multiple values for the same page feed '{page_feed_asset_set_name}'!\n"

    page_feed_template_row = page_feed_rows.iloc[0]
    custom_labels_values = [
        page_feed_template_row[col]
        for col in page_feed_rows.columns
        if col.startswith("Custom Label")
    ]
    page_feed_rows = page_feeds_df[
        page_feeds_df["Custom Label"].isin(custom_labels_values)
    ]

    if page_feed_rows.empty:
        return f"No page feed data found for page feed '{page_feed_asset_set_name}'\n"

    page_feed_url_and_label_df = page_feed_rows[["Page URL", "Custom Label"]]

    gads_page_urls_and_labels_df = _get_page_feed_items(
        user_id=user_id,
        conv_id=conv_id,
        customer_id=customer_id,
        login_customer_id=login_customer_id,
        asset_set_resource_name=page_feed_asset_set["resourceName"],
    )

    for df in [page_feed_url_and_label_df, gads_page_urls_and_labels_df]:
        df["Page URL"] = df["Page URL"].str.rstrip("/")

    missing_page_urls = page_feed_url_and_label_df[
        ~page_feed_url_and_label_df["Page URL"].isin(
            gads_page_urls_and_labels_df["Page URL"]
        )
    ]
    extra_page_urls = gads_page_urls_and_labels_df[
        ~gads_page_urls_and_labels_df["Page URL"].isin(
            page_feed_url_and_label_df["Page URL"]
        )
    ]

    if missing_page_urls.empty and extra_page_urls.empty:
        return "No changes needed for page feed 'fastagency-reference'\n"

    return_value = f"Page feed '{page_feed_asset_set_name}' changes:\n"
    if not missing_page_urls.empty:
        url_and_labels = missing_page_urls.set_index("Page URL")[
            "Custom Label"
        ].to_dict()
        add_model = AddPageFeedItems(
            login_customer_id=login_customer_id,
            customer_id=customer_id,
            asset_set_resource_name=page_feed_asset_set["resourceName"],
            urls_and_labels=url_and_labels,
        )
        response = google_ads_post_or_get(
            user_id=user_id,
            conv_id=conv_id,
            model=add_model,
            recommended_modifications_and_answer_list=[],
            already_checked_clients_approval=True,
            endpoint="/add-items-to-page-feed",
        )
        if isinstance(response, dict):
            raise ValueError(response)
        return_value += response

    if not extra_page_urls.empty:
        # Remove extra page urls
        for row in extra_page_urls.iterrows():
            id = row[1]["Id"]
            remove_model = RemoveResource(
                customer_id=customer_id,
                parent_id=page_feed_asset_set["id"],
                resource_id=id,
                resource_type="asset_set_asset",
            )

            response = google_ads_create_update(
                user_id=user_id,
                conv_id=conv_id,
                recommended_modifications_and_answer_list=[],
                already_checked_clients_approval=True,
                ad=remove_model,
                login_customer_id=customer_id,
                endpoint="/remove-google-ads-resource",
            )
            if isinstance(response, dict):
                return_value += f"Failed to remove page feed item with id {id} - {row[1]['Page URL']}\n"
            else:
                return_value += response

    return return_value


def _sync_page_feed_asset_sets(
    user_id: int,
    conv_id: int,
    customer_id: str,
    login_customer_id: str,
    page_feeds_and_accounts_templ_df: pd.DataFrame,
    page_feeds_df: pd.DataFrame,
    page_feed_asset_sets: Dict[str, Dict[str, str]],
) -> str:
    return_value = ""
    for page_feed_asset_set_name, page_feed_asset_set in page_feed_asset_sets.items():
        return_value += _sync_page_feed_asset_set(
            user_id=user_id,
            conv_id=conv_id,
            customer_id=customer_id,
            login_customer_id=login_customer_id,
            page_feeds_and_accounts_templ_df=page_feeds_and_accounts_templ_df,
            page_feeds_df=page_feeds_df,
            page_feed_asset_set_name=page_feed_asset_set_name,
            page_feed_asset_set=page_feed_asset_set,
        )

    return "All page feeds have been updated."
    # return return_value


def update_page_feeds(
    customer_id: Annotated[str, "Customer Id to update"],
    login_customer_id: Annotated[str, "Login Customer Id (Manager Account)"],
    context: PageFeedTeamContext,
) -> str:
    if context.page_feeds_and_accounts_templ_df is None:
        return f"Please validate the page feed data first by running the '{validate_page_feed_data.__name__}' function."

    page_feed_asset_sets = _get_page_feed_asset_sets(
        user_id=context.user_id,
        conv_id=context.conv_id,
        customer_id=customer_id,
        login_customer_id=login_customer_id,
    )
    if len(page_feed_asset_sets) == 0:
        return f"No page feeds found for customer id {customer_id}."

    return _sync_page_feed_asset_sets(
        user_id=context.user_id,
        conv_id=context.conv_id,
        customer_id=customer_id,
        login_customer_id=login_customer_id,
        page_feeds_and_accounts_templ_df=context.page_feeds_and_accounts_templ_df,
        page_feeds_df=context.page_feeds_df,
        page_feed_asset_sets=page_feed_asset_sets,
    )


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
    toolbox.add_function(VALIDATE_PAGE_FEED_DATA_DESCRIPTION)(validate_page_feed_data)
    toolbox.add_function(UPDATE_PAGE_FEED_DESCRIPTION)(update_page_feeds)

    toolbox.add_function(
        description=CHANGE_GOOGLE_ADS_ACCOUNT_DESCRIPTION,
        name="change_google_ads_account_or_refresh_token",
    )(change_google_account)

    return toolbox
