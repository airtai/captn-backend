from typing import Annotated

from ..toolboxes import Toolbox
from ._functions import BaseContext

__all__ = ("create_google_ads_expert_toolbox",)

CREATE_GOOGLE_ADS_RESOURCES_DESCRIPTION = "Creates Google Ads resources"


def create_google_ads_resources(
    customer_id: Annotated[
        str,
        "The ID of the Google Ads customer account (for now use '123')",
    ],
    spreadsheet_id: Annotated[
        str,
        "The ID of the spreadsheet to retrieve data from",
    ],
    ads_title: Annotated[
        str,
        "The title of the sheet with ads",
    ],
    keywords_title: Annotated[
        str,
        "The title of the sheet with keywords",
    ],
    context: BaseContext,
) -> str:
    return "Resources have been created"


def create_google_ads_expert_toolbox(
    user_id: int,
    conv_id: int,
) -> Toolbox:
    toolbox = Toolbox()

    context = BaseContext(
        user_id=user_id,
        conv_id=conv_id,
    )
    toolbox.set_context(context)

    toolbox.add_function(CREATE_GOOGLE_ADS_RESOURCES_DESCRIPTION)(
        create_google_ads_resources
    )

    return toolbox
