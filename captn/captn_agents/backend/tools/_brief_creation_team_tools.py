from dataclasses import dataclass
from typing import Type

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from ..teams._team import Team
from ..toolboxes import Toolbox
from ._functions import (
    get_info_from_the_web_page,
    get_info_from_the_web_page_description,
    reply_to_client,
    reply_to_client_description,
)


@dataclass
class Context:
    user_id: int
    conv_id: int


class DelegateTask(BaseModel):
    team_name: Annotated[str, Field(..., description="The name of the team")]
    task: Annotated[str, Field(..., description="The task to be delagated")]
    customers_business_brief: Annotated[
        str,
        Field(
            ...,
            min_length=30,
            description="The brief containing the main information about the customer's business",
        ),
    ]
    summary_from_web_page: Annotated[
        str,
        Field(..., min_length=30, description="The summary of the web page content"),
    ]


def create_brief_creation_team_toolbox(
    user_id: int,
    conv_id: int,
) -> Toolbox:
    toolbox = Toolbox()

    context = Context(
        user_id=user_id,
        conv_id=conv_id,
    )
    toolbox.set_context(context)

    @toolbox.add_function(
        "Get the TEMPLATE for the customer brief you will need to create"
    )
    def get_brief_template(
        team_name: Annotated[
            str,
            "The name of the team which will be responsible for the task. Make sure to select the right team for the task!",
        ],
    ) -> str:
        team_class: Type[Team] = Team.get_class_by_registred_team_name(team_name)
        return team_class.get_brief_template()

    @toolbox.add_function("Delegate the task to the selected team")
    def delagate_task(
        delegate_task: DelegateTask,
        context: Context,
    ) -> str:
        user_id = context.user_id
        conv_id = context.conv_id

        team_class: Type[Team] = Team.get_class_by_registred_team_name(
            delegate_task.team_name
        )

        final_task = f"Here is the customer brief:\n{delegate_task.customers_business_brief}\n\nAdditional info from the web page:\n{delegate_task.summary_from_web_page}\n\nAnd the task is following:\n{delegate_task.task}"

        # Remove the user_id-conv_id pair from the team so that the new team can be created
        Team.pop_team(user_id=user_id, conv_id=conv_id)
        team = team_class(  # type: ignore
            task=final_task,
            user_id=user_id,
            conv_id=conv_id,
        )

        team.initiate_chat()
        # the last message is TeamResponse in json encoded string
        last_message = team.get_last_message(add_prefix=False)
        return last_message

    toolbox.add_function(get_info_from_the_web_page_description)(
        get_info_from_the_web_page
    )

    toolbox.add_function(reply_to_client_description)(reply_to_client)

    return toolbox
