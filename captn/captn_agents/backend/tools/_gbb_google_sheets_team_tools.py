from dataclasses import dataclass
from typing import Annotated, Any, Dict, List, Union

import pandas as pd
from pydantic import BaseModel, Field
from requests import get as requests_get

from captn.google_ads.client import check_for_client_approval
from google_ads.model import (
    Campaign,
)

from ....google_ads.client import google_ads_create_update
from ..toolboxes import Toolbox
from ._campaign_creation_team_tools import (
    AdGroupAdForCreation,
    AdGroupCriterionForCreation,
    AdGroupForCreation,
    AdGroupWithAdAndKeywords,
    _create_ad_group_with_ad_and_keywords,
)
from ._functions import (
    REPLY_TO_CLIENT_DESCRIPTION,
    Context,
    ask_client_for_permission,
    ask_client_for_permission_description,
    reply_to_client,
)
from ._google_ads_team_tools import (
    get_resource_id_from_response,
    list_accessible_customers,
    list_accessible_customers_description,
)

__all__ = ("create_google_sheets_team_toolbox",)

CREATE_GOOGLE_ADS_RESOURCES_DESCRIPTION = "Creates Google Ads resources"


class GoogleAdsResources(BaseModel):
    customer_id: Annotated[
        str, Field(..., description="The ID of the Google Ads customer account")
    ]
    spreadsheet_id: Annotated[
        str, Field(..., description="The ID of the spreadsheet to retrieve data from")
    ]
    ads_title: Annotated[str, Field(..., description="The title of the sheet with ads")]
    keywords_title: Annotated[
        str, Field(..., description="The title of the sheet with keywords")
    ]


class GoogleSheetValues(BaseModel):
    values: List[List[Any]] = Field(
        ..., title="Values", description="Values written in the Google Sheet."
    )


def _get_sheet_data(
    base_url: str, user_id: int, spreadsheet_id: str, title: str
) -> Dict[str, List[List[Any]]]:
    params: Dict[str, Union[int, str]] = {
        "user_id": user_id,
        "spreadsheet_id": spreadsheet_id,
        "title": title,
    }
    response = requests_get(f"{base_url}/get-sheet", params=params, timeout=60)
    if not response.ok:
        raise ValueError(response.content)

    return response.json()  # type: ignore[no-any-return]


@dataclass
class GoogleSheetsTeamContext(Context):
    google_sheets_api_url: str


KEYWORDS_MANDATORY_COLUMNS = [
    "Campaign Name",
    "Campaign Budget",
    "Ad Group Name",
    "Match Type",
    "Keyword",
]
ADS_MANDATORY_COLUMNS = [
    "Campaign Name",
    "Campaign Budget",
    "Ad Group Name",
    "Match Type",
    "Headline 1",
    "Headline 2",
    "Headline 3",
    "Description Line 1",
    "Description Line 2",
    "Path 1",
    "Final URL",
]


def _check_mandatory_columns(
    df: pd.DataFrame, mandatory_columns: List[str], table_title: str
) -> str:
    missing_columns = [col for col in mandatory_columns if col not in df.columns]
    if missing_columns:
        return f"{table_title} is missing columns: {missing_columns}"
    return ""


def create_google_ads_resources(
    google_ads_resources: GoogleAdsResources,
    context: GoogleSheetsTeamContext,
) -> Union[Dict[str, Any], str]:
    error_msg = check_for_client_approval(
        modification_function_parameters=google_ads_resources.model_dump(),
        recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
    )
    if error_msg:
        raise ValueError(error_msg)

    ads_data_dict = _get_sheet_data(
        base_url=context.google_sheets_api_url,
        user_id=context.user_id,
        spreadsheet_id=google_ads_resources.spreadsheet_id,
        title=google_ads_resources.ads_title,
    )
    keywords_data_dict = _get_sheet_data(
        base_url=context.google_sheets_api_url,
        user_id=context.user_id,
        spreadsheet_id=google_ads_resources.spreadsheet_id,
        title=google_ads_resources.keywords_title,
    )

    ads_values = GoogleSheetValues(**ads_data_dict)
    keywords_values = GoogleSheetValues(**keywords_data_dict)

    ads_df = pd.DataFrame(
        ads_values.values[1:],
        columns=ads_values.values[0],
    )
    keywords_df = pd.DataFrame(
        keywords_values.values[1:],
        columns=keywords_values.values[0],
    )
    mandatory_columns_error_msg = _check_mandatory_columns(
        ads_df, ADS_MANDATORY_COLUMNS, google_ads_resources.ads_title
    )
    mandatory_columns_error_msg += _check_mandatory_columns(
        keywords_df, KEYWORDS_MANDATORY_COLUMNS, google_ads_resources.keywords_title
    )
    if mandatory_columns_error_msg:
        raise ValueError(mandatory_columns_error_msg)

    campaign_names_ad_budgets = ads_df[
        ["Campaign Name", "Campaign Budget"]
    ].drop_duplicates()

    created_campaign_names_and_ids = {}
    for campaign_name, campaign_budget in campaign_names_ad_budgets.values:
        budget_amount_micros = int(campaign_budget) * 1_000_000

        campaign = Campaign(
            customer_id=google_ads_resources.customer_id,
            name=campaign_name,
            budget_amount_micros=budget_amount_micros,
            status="PAUSED",
            network_settings_target_google_search=True,
            network_settings_target_search_network=True,
            network_settings_target_content_network=True,
        )
        response = google_ads_create_update(
            user_id=context.user_id,
            conv_id=context.conv_id,
            recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
            ad=campaign,
            endpoint="/create-campaign",
            already_checked_clients_approval=True,
        )

        if not isinstance(response, str):
            return response
        else:
            campaign_id = get_resource_id_from_response(response)
            created_campaign_names_and_ids[campaign_name] = campaign_id

    for _, row in ads_df.iterrows():
        headlines = [
            row[col] for col in row.index if col.lower().startswith("headline")
        ]
        descriptions = [
            row[col] for col in row.index if col.lower().startswith("description")
        ]

        path1 = row.get("Path 1", None)
        path2 = row.get("Path 2", None)
        final_url = row.get("Final URL")

        campaign_id = created_campaign_names_and_ids[row["Campaign Name"]]
        ad_group = AdGroupForCreation(
            customer_id=google_ads_resources.customer_id,
            campaign_id=campaign_id,
            name=row["Ad Group Name"],
            status="ENABLED",
        )

        ad_group_ad = AdGroupAdForCreation(
            customer_id=google_ads_resources.customer_id,
            campaign_id=campaign_id,
            status="ENABLED",
            headlines=headlines,
            descriptions=descriptions,
            path1=path1,
            path2=path2,
            final_url=final_url,
        )

        match_type = row["Match Type"]
        ad_group_name = row["Ad Group Name"]
        ad_group_keywords = keywords_df[keywords_df["Ad Group Name"] == ad_group_name]
        keywords_list = ad_group_keywords["Keyword"].tolist()
        ad_group_keywords = []
        for keyword in keywords_list:
            ad_group_keywords.append(
                AdGroupCriterionForCreation(
                    customer_id=google_ads_resources.customer_id,
                    campaign_id=campaign_id,
                    status="ENABLED",
                    keyword_text=keyword,
                    keyword_match_type=match_type.upper(),
                )
            )

        ad_group_with_ad_and_keywords = AdGroupWithAdAndKeywords(
            customer_id=google_ads_resources.customer_id,
            campaign_id=campaign_id,
            ad_group=ad_group,
            ad_group_ad=ad_group_ad,
            keywords=ad_group_keywords,
        )

    return _create_ad_group_with_ad_and_keywords(
        ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
        context=context,
    )


def create_google_sheets_team_toolbox(
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
    toolbox.add_function(list_accessible_customers_description)(
        list_accessible_customers
    )
    toolbox.add_function(CREATE_GOOGLE_ADS_RESOURCES_DESCRIPTION)(
        create_google_ads_resources
    )

    return toolbox
