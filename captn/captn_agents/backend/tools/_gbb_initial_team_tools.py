from ..toolboxes import Toolbox
from ._brief_creation_team_tools import (
    DELEGATE_TASK_DESCRIPTION,
    GET_BRIEF_TEMPLATE_DESCRIPTION,
    Context,
    delagate_task,
    get_brief_template,
)
from ._functions import REPLY_TO_CLIENT_DESCRIPTION, reply_to_client


def create_gbb_initial_team_toolbox(
    user_id: int,
    conv_id: int,
    initial_brief: str,
) -> Toolbox:
    toolbox = Toolbox()

    context = Context(
        user_id=user_id,
        conv_id=conv_id,
        initial_brief=initial_brief,
        get_info_from_web_page_result="Web page will not be scraped in this task.",
    )
    toolbox.set_context(context)

    toolbox.add_function(GET_BRIEF_TEMPLATE_DESCRIPTION)(get_brief_template)
    toolbox.add_function(DELEGATE_TASK_DESCRIPTION)(delagate_task)
    toolbox.add_function(REPLY_TO_CLIENT_DESCRIPTION)(reply_to_client)

    return toolbox
