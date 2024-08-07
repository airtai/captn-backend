from dataclasses import dataclass, field
from typing import Callable, Dict, Type

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from ...model import SmartSuggestions
from ..teams._team import Team
from ..toolboxes import Toolbox
from ._functions import (
    LAST_MESSAGE_BEGINNING,
    MAX_LINKS_TO_CLICK_DESCRIPTION,
    MIN_RELEVANT_PAGES_DESCRIPTION,
    REPLY_TO_CLIENT_DESCRIPTION,
    BaseContext,
    get_get_info_from_the_web_page,
    get_info_from_the_web_page_description,
    reply_to_client,
)

__all__ = (
    "Context",
    "DelegateTask",
    "DELEGATE_TASK_DESCRIPTION",
    "delagate_task",
    "GET_BRIEF_TEMPLATE_DESCRIPTION",
    "get_brief_template",
)


@dataclass
class Context(BaseContext):
    initial_brief: str
    function_call_counter: Dict[str, bool] = field(default_factory=dict)
    get_info_from_web_page_result: str = ""


class DelegateTask(BaseModel):
    team_name: Annotated[str, Field(..., description="The name of the team")]
    task: Annotated[str, Field(..., description="The task to be delagated")]
    customers_business_brief: Annotated[
        str,
        Field(
            ...,
            min_length=30,
            description="""Updated customer brief. The brief should contain all important information received from the previous team along with the new information you have retrieved.
You must fill in all the fields. NEVER write [Insert client's business]!! You are responsible for filling in the information!""",
        ),
    ]


class WebPageInfo:
    def get_info_from_the_web_page_f(self) -> Callable[[str, int, int], str]:
        return get_get_info_from_the_web_page()


DELEGATE_TASK_ERROR_MESSAGE = "An error occurred while trying to delegate the task to the selected team. Please try again."


def _change_the_team_and_start_new_chat(
    user_id: int, conv_id: int, final_task: str, team_class: Type[Team]
) -> str:
    # Remove the user_id-conv_id pair from the team so that the new team can be created
    Team.pop_team(user_id=user_id, conv_id=conv_id)
    team = team_class(  # type: ignore
        task=final_task,
        user_id=user_id,
        conv_id=conv_id,
    )
    if team.toolbox is None:
        raise ValueError("Team toolbox is not set!")

    try:
        team.initiate_chat()
    except Exception as e:
        print(
            f"An error occurred while trying to execute delegate_task: {type(e)}, {e}"
        )
        smart_suggestions = SmartSuggestions(
            suggestions=["Try again"], type="oneOf"
        ).model_dump()
        return reply_to_client(
            message=DELEGATE_TASK_ERROR_MESSAGE,
            completed=False,
            smart_suggestions=smart_suggestions,
            context=team.toolbox._context,  # type: ignore[arg-type]
        )
    # the last message is TeamResponse in json encoded string
    last_message = team.get_last_message(add_prefix=False)
    return last_message


DELEGATE_TASK_DESCRIPTION = "Delegate the task to the selected team. Use this function only once you have scraped the web page and filled in the customer brief!"


def delagate_task(
    task_and_context_to_delegate: Annotated[
        DelegateTask,
        "All the information needed to delegate the task. Make sure to fill in all the fields!",
    ],
    context: Context,
) -> str:
    get_info_from_web_page_result = context.get_info_from_web_page_result
    if get_info_from_web_page_result == "":
        return "You need to scrape the web page first by using the get_info_from_the_web_page command."

    user_id = context.user_id
    conv_id = context.conv_id

    team_class: Type[Team] = Team.get_class_by_registred_team_name(
        task_and_context_to_delegate.team_name
    )

    final_task = f"""Here is the customer brief:
{task_and_context_to_delegate.customers_business_brief}

Additional info from the web page:
{get_info_from_web_page_result}

And the task is following:
{task_and_context_to_delegate.task}
"""

    last_message = _change_the_team_and_start_new_chat(
        user_id=user_id,
        conv_id=conv_id,
        final_task=final_task,
        team_class=team_class,
    )
    return last_message


GET_BRIEF_TEMPLATE_DESCRIPTION = (
    "Get the TEMPLATE for the customer brief you will need to create"
)


def get_brief_template(
    team_name: Annotated[
        str,
        "The name of the team which will be responsible for the task. Make sure to select the right team for the task!",
    ],
    context: Context,
) -> str:
    counter = context.function_call_counter
    key = f"get_brief_template_{team_name}"
    if key in counter:
        return "You have already received the brief template, please sproceed with the task."

    counter[key] = True
    team_class: Type[Team] = Team.get_class_by_registred_team_name(team_name)
    brief_template = f"""Here is the customer brief we have received from the previous team:

{context.initial_brief}
Use this information to fill in the rest of the fields in the customer brief template.


Here is a template for the customer brief you will need to create:
{team_class.get_brief_template()}
"""

    return brief_template


def create_brief_creation_team_toolbox(
    user_id: int,
    conv_id: int,
    initial_brief: str,
) -> Toolbox:
    toolbox = Toolbox()

    context = Context(
        user_id=user_id,
        conv_id=conv_id,
        initial_brief=initial_brief,
    )
    toolbox.set_context(context)
    web_page_info = WebPageInfo()
    web_page_info_f = web_page_info.get_info_from_the_web_page_f()

    toolbox.add_function(GET_BRIEF_TEMPLATE_DESCRIPTION)(get_brief_template)
    toolbox.add_function(DELEGATE_TASK_DESCRIPTION)(delagate_task)

    @toolbox.add_function(get_info_from_the_web_page_description)
    def get_info_from_the_web_page(
        url: Annotated[str, "The url of the web page which needs to be summarized"],
        max_links_to_click: Annotated[
            int,
            MAX_LINKS_TO_CLICK_DESCRIPTION,
        ],
        min_relevant_pages: Annotated[int, MIN_RELEVANT_PAGES_DESCRIPTION],
        context: Context,
    ) -> str:
        result = web_page_info_f(  # type: ignore[call-arg]
            url=url,
            max_links_to_click=max_links_to_click,
            min_relevant_pages=min_relevant_pages,
        )

        if LAST_MESSAGE_BEGINNING in result:
            context.get_info_from_web_page_result += (
                result.replace(LAST_MESSAGE_BEGINNING, "") + "\n\n"
            )

        result += """\n\nPlease use the rely_to_client to present what you have found on the web page to the client.

Use smart suggestions with type 'manyOf' to ask the client in which pages they are interested in.
Each relevant page should be one smart suggestion.
Additionally, add to smart suggestions 'Proceed with the task without further web page scraping' to allow the client to proceed without further web page scraping.
If the client chooses this option do NOT use the 'get_info_from_the_web_page' command again.
If the client does not choose this option, you can use the 'get_info_from_the_web_page' if you think you need more information for the selected pages.
"""
        return result

    toolbox.add_function(REPLY_TO_CLIENT_DESCRIPTION)(reply_to_client)

    return toolbox
