from dataclasses import dataclass
from typing import Annotated, Any, Dict, List, Tuple, Union

import pandas as pd
from pydantic import BaseModel, Field
from requests import get as requests_get

from captn.google_ads.client import check_for_client_approval
from google_ads.model import (
    AdGroupCriterion,
    Campaign,
    CampaignCriterion,
)

from ....google_ads.client import google_ads_create_update
from ....google_ads.client import (
    list_accessible_customers_with_account_types as list_accessible_customers_with_account_types_client,
)
from ....google_ads.client import (
    list_sub_accounts as list_sub_accounts_client,
)
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
)

__all__ = ("create_google_sheets_team_toolbox",)

CREATE_GOOGLE_ADS_RESOURCES_DESCRIPTION = "Creates Google Ads resources"


class GoogleAdsResources(BaseModel):
    login_customer_id: Annotated[
        str,
        Field(
            ...,
            description="The ID of the Google Ads manager account. If customer_id is not a part of a manager account, use the same ID for both login_customer_id and customer_id.",
        ),
    ]
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
    "Level",
    "Negative",
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


def _validate_and_convert_to_df(
    google_ads_resources: GoogleAdsResources,
    context: GoogleSheetsTeamContext,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
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

    return ads_df, keywords_df


def _create_campaign(
    campaign_name: str,
    campaign_budget: str,
    customer_id: str,
    context: GoogleSheetsTeamContext,
) -> Union[Dict[str, Any], str]:
    budget_amount_micros = int(campaign_budget) * 1_000_000

    campaign = Campaign(
        customer_id=customer_id,
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

    return response


def _create_negative_campaign_keywords(
    customer_id: str,
    campaign_id: str,
    campaign_name: str,
    keywords_df: pd.DataFrame,
    context: GoogleSheetsTeamContext,
) -> str:
    negative_campaign_keywords = keywords_df[
        (keywords_df["Campaign Name"] == campaign_name)
        & (keywords_df["Level"] == "Campaign")
        & (keywords_df["Negative"])
    ]
    final_response = ""
    for _, row in negative_campaign_keywords.iterrows():
        response = google_ads_create_update(
            user_id=context.user_id,
            conv_id=context.conv_id,
            recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
            ad=CampaignCriterion(
                customer_id=customer_id,
                campaign_id=campaign_id,
                status="ENABLED",
                keyword_match_type=row["Match Type"].upper(),
                keyword_text=row["Keyword"],
                negative=True,
            ),
            endpoint="/add-negative-keywords-to-campaign",
            already_checked_clients_approval=True,
        )
        final_response += f"Negative campaign keyword {row['Keyword']}\n{response}\n"

    return final_response


def _create_negative_ad_group_keywords(
    customer_id: str,
    campaign_id: str,
    ad_group_id: str,
    ad_group_name: str,
    keywords_df: pd.DataFrame,
    context: GoogleSheetsTeamContext,
) -> str:
    ad_group_negative_keywords = keywords_df[
        (keywords_df["Ad Group Name"] == ad_group_name) & (keywords_df["Negative"])
    ]
    final_response = ""
    for _, row in ad_group_negative_keywords.iterrows():
        negative_keyword = AdGroupCriterion(
            customer_id=customer_id,
            campaign_id=campaign_id,
            ad_group_id=ad_group_id,
            status="ENABLED",
            keyword_text=row["Keyword"],
            keyword_match_type=row["Match Type"].upper(),
            negative=True,
        )

        response = google_ads_create_update(
            user_id=context.user_id,
            conv_id=context.conv_id,
            recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
            ad=negative_keyword,
            endpoint="/add-keywords-to-ad-group",
            already_checked_clients_approval=True,
        )

        final_response += f"Negative ad group keyword {row['Keyword']}\n{response}\n"
    return final_response


def _create_ad_group_with_ad_and_keywords_helper(
    customer_id: str,
    campaign_id: str,
    ad_group_name: str,
    match_type: str,
    keywords_df: pd.DataFrame,
    ad_group_ad: AdGroupAdForCreation,
    context: GoogleSheetsTeamContext,
) -> str:
    ad_group = AdGroupForCreation(
        customer_id=customer_id,
        campaign_id=campaign_id,
        name=ad_group_name,
        status="ENABLED",
    )

    ad_group_positive_keywords = keywords_df[
        (keywords_df["Ad Group Name"] == ad_group_name) & (~keywords_df["Negative"])
    ]
    positive_keywords_list = ad_group_positive_keywords["Keyword"].tolist()
    ad_group_positive_keywords = []
    for keyword in positive_keywords_list:
        ad_group_positive_keywords.append(
            AdGroupCriterionForCreation(
                customer_id=customer_id,
                campaign_id=campaign_id,
                status="ENABLED",
                keyword_text=keyword,
                keyword_match_type=match_type.upper(),
            )
        )

    ad_group_with_ad_and_keywords = AdGroupWithAdAndKeywords(
        customer_id=customer_id,
        campaign_id=campaign_id,
        ad_group=ad_group,
        ad_group_ad=ad_group_ad,
        keywords=ad_group_positive_keywords,
    )

    response = _create_ad_group_with_ad_and_keywords(
        ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
        context=context,
    )

    if not isinstance(response, str):
        raise ValueError(response)

    final_response = response + "\n"

    response = _create_negative_ad_group_keywords(
        customer_id=customer_id,
        campaign_id=campaign_id,
        ad_group_id=ad_group_ad.ad_group_id,  # type: ignore[arg-type]
        ad_group_name=ad_group_name,
        keywords_df=keywords_df,
        context=context,
    )
    final_response += response
    return final_response


def create_google_ads_resources(
    google_ads_resources: GoogleAdsResources,
    context: GoogleSheetsTeamContext,
) -> Union[Dict[str, Any], str]:
    ads_df, keywords_df = _validate_and_convert_to_df(
        google_ads_resources=google_ads_resources,
        context=context,
    )

    keywords_df["Negative"] = keywords_df["Negative"].str.upper().eq("TRUE")
    campaign_names_ad_budgets = ads_df[
        ["Campaign Name", "Campaign Budget"]
    ].drop_duplicates()

    final_response = ""
    created_campaign_names_and_ids = {}
    for campaign_name, campaign_budget in campaign_names_ad_budgets.values:
        response = _create_campaign(
            campaign_name=campaign_name,
            campaign_budget=campaign_budget,
            customer_id=google_ads_resources.customer_id,
            context=context,
        )
        final_response += f"Campaign {campaign_name}\n{response}\n"

        if not isinstance(response, str):
            return response
        else:
            campaign_id = get_resource_id_from_response(response)
            created_campaign_names_and_ids[campaign_name] = campaign_id

        final_response += _create_negative_campaign_keywords(
            customer_id=google_ads_resources.customer_id,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            keywords_df=keywords_df,
            context=context,
        )

    created_ad_group_names_and_ids: Dict[str, str] = {}
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

        # If ad group already exists, create only ad group ad
        if row["Ad Group Name"] in created_ad_group_names_and_ids:
            ad_group_ad.ad_group_id = created_ad_group_names_and_ids[
                row["Ad Group Name"]
            ]
            response = google_ads_create_update(
                user_id=context.user_id,
                conv_id=context.conv_id,
                recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
                ad=ad_group_ad,
                endpoint="/create-ad-group-ad",
                already_checked_clients_approval=True,
            )
            if not isinstance(response, str):
                raise ValueError(response)
            final_response += f"Ad group ad\n{response}\n"
        # Otherwise, create ad group, ad group ad, and keywords
        else:
            final_response += _create_ad_group_with_ad_and_keywords_helper(
                customer_id=google_ads_resources.customer_id,
                campaign_id=campaign_id,
                ad_group_name=row["Ad Group Name"],
                match_type=row["Match Type"],
                keywords_df=keywords_df,
                ad_group_ad=ad_group_ad,
                context=context,
            )
            created_ad_group_names_and_ids[row["Ad Group Name"]] = (
                ad_group_ad.ad_group_id  # type: ignore[assignment]
            )

    return final_response


LIST_ACCESSIBLE_CUSTOMERS_WITH_ACCOUNT_TYPES_DESCRIPTION = (
    "List accessible customers with account types"
)


def list_accessible_customers_with_account_types(
    context: Context,
) -> Dict[str, Any]:
    return list_accessible_customers_with_account_types_client(
        user_id=context.user_id,
        conv_id=context.conv_id,
    )


LIST_SUB_ACCOUNTS_DESCRIPTION = """Use this function to list sub accounts of a Google Ads manager account.
login_customer_id is the ID of the Google Ads manager account, you can get all available accounts by using list_accessible_customers_with_account_types function.
customer_id is the ID of the Google Ads account you want to list sub accounts of."""


def list_sub_accounts(
    login_customer_id: Annotated[
        str, "The ID of the Google Ads manager customer account"
    ],
    customer_id: Annotated[
        str,
        "The ID of the Google Ads customer account whose sub accounts you want to list",
    ],
    context: Context,
) -> Any:
    return list_sub_accounts_client(
        user_id=context.user_id,
        login_customer_id=login_customer_id,
        customer_id=customer_id,
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
    toolbox.add_function(LIST_ACCESSIBLE_CUSTOMERS_WITH_ACCOUNT_TYPES_DESCRIPTION)(
        list_accessible_customers_with_account_types
    )
    toolbox.add_function(LIST_SUB_ACCOUNTS_DESCRIPTION)(list_sub_accounts)
    toolbox.add_function(CREATE_GOOGLE_ADS_RESOURCES_DESCRIPTION)(
        create_google_ads_resources
    )

    return toolbox
