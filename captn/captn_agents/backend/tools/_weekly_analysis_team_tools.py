from typing import Any, Dict, List, Optional, Tuple

from ..toolboxes import Toolbox
from ._functions import (
    Context,
    get_get_info_from_the_web_page,
    get_info_from_the_web_page_description,
    send_email,
    send_email_description,
)
from ._google_ads_team_tools import (
    execute_query,
    execute_query_description,
    list_accessible_customers,
    list_accessible_customers_description,
)

__all__ = ("create_weekly_analysis_team_toolbox",)


def create_weekly_analysis_team_toolbox(
    user_id: int,
    conv_id: int,
    recommended_modifications_and_answer_list: List[
        Tuple[Dict[str, Any], Optional[str]]
    ],
) -> Toolbox:
    toolbox = Toolbox()

    context = Context(
        user_id=user_id,
        conv_id=conv_id,
        recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
        get_only_non_manager_accounts=True,
        toolbox=toolbox,
    )
    toolbox.set_context(context)

    toolbox.add_function(list_accessible_customers_description)(
        list_accessible_customers
    )
    toolbox.add_function(execute_query_description)(execute_query)
    toolbox.add_function(get_info_from_the_web_page_description)(
        get_get_info_from_the_web_page()
    )
    toolbox.add_function(send_email_description)(send_email)

    return toolbox
