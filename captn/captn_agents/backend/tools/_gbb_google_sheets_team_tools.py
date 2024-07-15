from dataclasses import dataclass
from typing import Annotated, Any, Dict, List, Union

import pandas as pd
from pydantic import BaseModel, Field
from requests import get as requests_get

from captn.google_ads.client import check_for_client_approval

from ..toolboxes import Toolbox
from ._functions import (
    REPLY_TO_CLIENT_DESCRIPTION,
    Context,
    ask_client_for_permission,
    ask_client_for_permission_description,
    reply_to_client,
)
from ._google_ads_team_tools import (
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
) -> str:
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

    print(ads_df)
    print(keywords_df)

    return "Resources have been created"


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
