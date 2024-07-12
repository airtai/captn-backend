from typing import Annotated, Any, Dict

from pydantic import BaseModel, Field

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


def create_google_ads_resources(
    google_ads_resources: GoogleAdsResources,
    context: Context,
) -> str:
    error_msg = check_for_client_approval(
        modification_function_parameters=google_ads_resources.model_dump(),
        recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
    )
    if error_msg:
        raise ValueError(error_msg)
    return "Resources have been created"


def create_google_sheets_team_toolbox(
    user_id: int,
    conv_id: int,
    kwargs: Dict[str, Any],
) -> Toolbox:
    toolbox = Toolbox()

    context = Context(
        user_id=user_id,
        conv_id=conv_id,
        recommended_modifications_and_answer_list=kwargs[
            "recommended_modifications_and_answer_list"
        ],
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
