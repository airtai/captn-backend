import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from autogen.formatting_utils import colored
from autogen.io.base import IOStream
from pydantic import BaseModel, Field
from pytz import timezone
from requests import get as requests_get

from captn.google_ads.client import check_for_client_approval
from google_ads.model import (
    AdGroupCriterion,
    Campaign,
    CampaignCriterion,
    RemoveResource,
)

from ....google_ads.client import (
    execute_query,
    google_ads_create_update,
)
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
    login_customer_id: Optional[str],
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
        login_customer_id=login_customer_id,
        endpoint="/create-campaign",
        already_checked_clients_approval=True,
    )

    return response


def _create_negative_campaign_keywords(
    customer_id: str,
    login_customer_id: Optional[str],
    campaign_id: str,
    keywords_df: pd.DataFrame,
    context: GoogleSheetsTeamContext,
) -> None:
    negative_campaign_keywords = keywords_df[
        (keywords_df["Level"] == "Campaign") & (keywords_df["Negative"])
    ]
    for _, row in negative_campaign_keywords.iterrows():
        google_ads_create_update(
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
            login_customer_id=login_customer_id,
            already_checked_clients_approval=True,
        )


def _create_negative_ad_group_keywords(
    customer_id: str,
    login_customer_id: Optional[str],
    campaign_id: str,
    ad_group_id: str,
    ad_group_keywords_df: pd.DataFrame,
    context: GoogleSheetsTeamContext,
) -> None:
    ad_group_negative_keywords = ad_group_keywords_df[
        (ad_group_keywords_df["Negative"])
    ]
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

        google_ads_create_update(
            user_id=context.user_id,
            conv_id=context.conv_id,
            recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
            ad=negative_keyword,
            endpoint="/add-keywords-to-ad-group",
            login_customer_id=login_customer_id,
            already_checked_clients_approval=True,
        )


def _create_ad_group_with_ad_and_keywords_helper(
    customer_id: str,
    login_customer_id: Optional[str],
    campaign_id: str,
    ad_group_name: str,
    match_type: str,
    ad_group_keywords_df: pd.DataFrame,
    ad_group_ad: AdGroupAdForCreation,
    context: GoogleSheetsTeamContext,
) -> None:
    ad_group = AdGroupForCreation(
        customer_id=customer_id,
        campaign_id=campaign_id,
        name=ad_group_name,
        status="ENABLED",
    )

    ad_group_positive_keywords = ad_group_keywords_df[
        (~ad_group_keywords_df["Negative"])
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
        login_customer_id=login_customer_id,
        remove_on_error=False,
    )

    if not isinstance(response, str):
        raise ValueError(response)

    _create_negative_ad_group_keywords(
        customer_id=customer_id,
        login_customer_id=login_customer_id,
        campaign_id=campaign_id,
        ad_group_id=ad_group_ad.ad_group_id,  # type: ignore[arg-type]
        ad_group_keywords_df=ad_group_keywords_df,
        context=context,
    )


def _get_alredy_existing_campaigns(
    df: pd.DataFrame,
    user_id: int,
    conv_id: int,
    customer_id: str,
    login_customer_id: str,
) -> List[str]:
    distinct_campaign_names = df["Campaign Name"].unique().tolist()
    distinct_campaign_names_str = ", ".join(
        [f"'{name}'" for name in distinct_campaign_names]
    )

    query = f"""SELECT campaign.id, campaign.name
FROM campaign
WHERE campaign.name IN ({distinct_campaign_names_str}) AND campaign.status != 'REMOVED'
"""  # nosec: [B608]
    response = execute_query(
        user_id=user_id,
        conv_id=conv_id,
        customer_ids=[customer_id],
        login_customer_id=login_customer_id,
        query=query,
    )
    if not isinstance(response, str):
        raise ValueError(response)

    response_json = json.loads(response.replace("'", '"'))
    alredy_existing_campaigns = [
        campaign["campaign"]["name"] for campaign in response_json[customer_id]
    ]
    return alredy_existing_campaigns


class ResourceCreationResponse(BaseModel):
    skip_campaigns: List[str]
    created_campaigns: List[str]
    failed_campaigns: Dict[str, str]

    def response(self) -> str:
        response = ""
        backslash_n = "\n"
        if self.created_campaigns:
            response += (
                f"Created campaigns:\n{backslash_n.join(self.created_campaigns)}\n\n"
            )
        else:
            response += "No campaigns were created.\n\n"
        if self.skip_campaigns:
            response += f"The following campaigns already exist:\n{backslash_n.join(self.skip_campaigns)}\n\n"
        if self.failed_campaigns:
            response += "Failed to create the following campaigns:\n"
            for failed_campaign, error in self.failed_campaigns.items():
                response += f"{failed_campaign}:\n{error}\n\n"
        return response


ZAGREB_TIMEZONE = timezone("Europe/Zagreb")


def _setup_campaign(
    customer_id: str,
    login_customer_id: str,
    campaign_name: str,
    campaign_budget: str,
    context: GoogleSheetsTeamContext,
    keywords_df: pd.DataFrame,
    ads_df: pd.DataFrame,
    iostream: IOStream,
) -> Tuple[bool, Optional[str]]:
    campaign_id = None
    created_campaign_names_and_ids: Dict[str, Dict[str, Any]] = {}
    try:
        response = _create_campaign(
            campaign_name=campaign_name,
            campaign_budget=campaign_budget,
            customer_id=customer_id,
            login_customer_id=login_customer_id,
            context=context,
        )

        if not isinstance(response, str):
            raise ValueError(response)
        else:
            campaign_id = get_resource_id_from_response(response)
            created_campaign_names_and_ids[campaign_name] = {
                "campaign_id": campaign_id,
                "ad_groups": {},
            }

        all_campaign_keywords = keywords_df[
            (keywords_df["Campaign Name"] == campaign_name)
        ]

        _create_negative_campaign_keywords(
            customer_id=customer_id,
            login_customer_id=login_customer_id,
            campaign_id=campaign_id,
            keywords_df=all_campaign_keywords,
            context=context,
        )

        for _, row in ads_df[ads_df["Campaign Name"] == campaign_name].iterrows():
            headlines = [
                row[col] for col in row.index if col.lower().startswith("headline")
            ]
            descriptions = [
                row[col] for col in row.index if col.lower().startswith("description")
            ]

            path1 = row.get("Path 1", None)
            path2 = row.get("Path 2", None)
            final_url = row.get("Final URL")

            campaign = created_campaign_names_and_ids[campaign_name]
            ad_group_ad = AdGroupAdForCreation(
                customer_id=customer_id,
                campaign_id=campaign_id,
                status="ENABLED",
                headlines=headlines,
                descriptions=descriptions,
                path1=path1,
                path2=path2,
                final_url=final_url,
            )

            # If ad group already exists, create only ad group ad
            if row["Ad Group Name"] in campaign["ad_groups"]:
                ad_group_ad.ad_group_id = campaign["ad_groups"][row["Ad Group Name"]]
                response = google_ads_create_update(
                    user_id=context.user_id,
                    conv_id=context.conv_id,
                    recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
                    ad=ad_group_ad,
                    endpoint="/create-ad-group-ad",
                    login_customer_id=login_customer_id,
                    already_checked_clients_approval=True,
                )
                if not isinstance(response, str):
                    raise ValueError(response)
            # Otherwise, create ad group, ad group ad, and keywords
            else:
                all_ad_group_keywords = all_campaign_keywords[
                    all_campaign_keywords["Ad Group Name"] == row["Ad Group Name"]
                ]
                _create_ad_group_with_ad_and_keywords_helper(
                    customer_id=customer_id,
                    login_customer_id=login_customer_id,
                    campaign_id=campaign_id,
                    ad_group_name=row["Ad Group Name"],
                    match_type=row["Match Type"],
                    ad_group_keywords_df=all_ad_group_keywords,
                    ad_group_ad=ad_group_ad,
                    context=context,
                )
                campaign["ad_groups"][row["Ad Group Name"]] = ad_group_ad.ad_group_id

        message = f"[{datetime.now(ZAGREB_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}] Created campaign: {campaign_name}"
        iostream.print(colored(message, "green"), flush=True)
        return True, None

    except Exception as e:
        error_msg = str(e)
        message = f"[{datetime.now(ZAGREB_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}] Failed to create campaign: {campaign_name}: {error_msg}"
        iostream.print(colored(message, "red"), flush=True)

        try:
            if campaign_id:
                remove_resource = RemoveResource(
                    customer_id=customer_id,
                    resource_id=campaign_id,
                    resource_type="campaign",
                )
                google_ads_create_update(
                    user_id=context.user_id,
                    conv_id=context.conv_id,
                    recommended_modifications_and_answer_list=[],
                    ad=remove_resource,
                    endpoint="/remove-google-ads-resource",
                    login_customer_id=login_customer_id,
                    already_checked_clients_approval=True,
                )
        except Exception as e:
            error_msg += f"\nFailed to remove campaign: {str(e)}"

        return False, error_msg


def _setup_campaigns(
    customer_id: str,
    login_customer_id: str,
    context: GoogleSheetsTeamContext,
    skip_campaigns: List[str],
    campaign_names_ad_budgets: pd.DataFrame,
    keywords_df: pd.DataFrame,
    ads_df: pd.DataFrame,
    iostream: IOStream,
) -> ResourceCreationResponse:
    created_campaigns: List[str] = []
    failed_campaigns: Dict[str, str] = {}
    for campaign_name, campaign_budget in campaign_names_ad_budgets.values:
        success, error_message = _setup_campaign(
            customer_id=customer_id,
            login_customer_id=login_customer_id,
            campaign_name=campaign_name,
            campaign_budget=campaign_budget,
            context=context,
            keywords_df=keywords_df,
            ads_df=ads_df,
            iostream=iostream,
        )

        if success:
            created_campaigns.append(campaign_name)
        else:
            failed_campaigns[campaign_name] = error_message  # type: ignore[assignment]

    resource_creation_response = ResourceCreationResponse(
        skip_campaigns=skip_campaigns,
        created_campaigns=created_campaigns,
        failed_campaigns=failed_campaigns,
    )

    return resource_creation_response


def _setup_campaigns_with_retry(
    customer_id: str,
    login_customer_id: str,
    context: GoogleSheetsTeamContext,
    skip_campaigns: List[str],
    campaign_names_ad_budgets: pd.DataFrame,
    keywords_df: pd.DataFrame,
    ads_df: pd.DataFrame,
    iostream: IOStream,
    retry_count: int = 2,
) -> ResourceCreationResponse:
    resource_creation_response = _setup_campaigns(
        customer_id=customer_id,
        login_customer_id=login_customer_id,
        context=context,
        skip_campaigns=skip_campaigns,
        campaign_names_ad_budgets=campaign_names_ad_budgets,
        keywords_df=keywords_df,
        ads_df=ads_df,
        iostream=iostream,
    )

    for i in range(retry_count):
        if not resource_creation_response.failed_campaigns:
            break

        # exponential backoff for retries
        time.sleep(2**i)

        iostream.print(
            colored(f"{i}. retry to create failed campaigns.", "yellow"), flush=True
        )
        retry_campaign_names_ad_budgets = campaign_names_ad_budgets[
            campaign_names_ad_budgets["Campaign Name"].isin(
                resource_creation_response.failed_campaigns.keys()
            )
        ]
        retry_resource_creation_response = _setup_campaigns(
            customer_id=customer_id,
            login_customer_id=login_customer_id,
            context=context,
            skip_campaigns=skip_campaigns,
            campaign_names_ad_budgets=retry_campaign_names_ad_budgets,
            keywords_df=keywords_df,
            ads_df=ads_df,
            iostream=iostream,
        )

        resource_creation_response.created_campaigns.extend(
            retry_resource_creation_response.created_campaigns
        )
        # Remove failed campaigns that were successfully created in the retry
        for campaign_name in retry_resource_creation_response.created_campaigns:
            resource_creation_response.failed_campaigns.pop(campaign_name)

        resource_creation_response.failed_campaigns.update(
            retry_resource_creation_response.failed_campaigns
        )
        retry_count -= 1

    return resource_creation_response


def create_google_ads_resources(
    google_ads_resources: GoogleAdsResources,
    context: GoogleSheetsTeamContext,
) -> Union[Dict[str, Any], str]:
    start_time = time.time()
    ads_df, keywords_df = _validate_and_convert_to_df(
        google_ads_resources=google_ads_resources,
        context=context,
    )
    ads_df = ads_df.map(lambda x: x.strip() if isinstance(x, str) else x)
    keywords_df = keywords_df.map(lambda x: x.strip() if isinstance(x, str) else x)

    keywords_df["Negative"] = keywords_df["Negative"].str.upper().eq("TRUE")
    campaign_names_ad_budgets = ads_df[
        ["Campaign Name", "Campaign Budget"]
    ].drop_duplicates()

    skip_campaigns = _get_alredy_existing_campaigns(
        ads_df,
        context.user_id,
        context.conv_id,
        google_ads_resources.customer_id,
        google_ads_resources.login_customer_id,
    )

    iostream = IOStream.get_default()

    if skip_campaigns:
        backslash_n = "\n"
        message = f"The following campaigns already exist:\n{backslash_n.join(skip_campaigns)}\n\n"
        iostream.print(colored(message, "yellow"), flush=True)
    message = "Creating campaigns and resources, usually takes 90 seconds to setup one campaign."
    iostream.print(colored(message, "yellow"), flush=True)

    campaign_names_ad_budgets = campaign_names_ad_budgets[
        ~campaign_names_ad_budgets["Campaign Name"].isin(skip_campaigns)
    ]

    resource_creation_response = _setup_campaigns_with_retry(
        customer_id=google_ads_resources.customer_id,
        login_customer_id=google_ads_resources.login_customer_id,
        context=context,
        skip_campaigns=skip_campaigns,
        campaign_names_ad_budgets=campaign_names_ad_budgets,
        keywords_df=keywords_df,
        ads_df=ads_df,
        iostream=iostream,
    )

    return (
        f"Execution time: {time.time() - start_time} seconds\n"
        + resource_creation_response.response()
    )


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
