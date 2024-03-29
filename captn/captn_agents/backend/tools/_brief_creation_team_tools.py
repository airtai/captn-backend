from typing import Type

from pydantic import BaseModel
from typing_extensions import Annotated

from ..teams._team import Team
from ..toolboxes import Toolbox


def _get_brief_template(
    team_name: str,
) -> str:
    team_class: Type[Team] = Team.get_class_by_name(team_name)
    return team_class.get_brief_template()


def _delagate_task(
    user_id: int,
    conv_id: int,
    team_name: str,
    task: str,
    customers_brief: str,
) -> str:
    team_class: Type[Team] = Team.get_class_by_name(team_name)

    final_task = f"Here is the customer brief:\n{customers_brief}\n\nAnd the task is following:\n{task}"
    team = team_class(  # type: ignore
        task=final_task,
        user_id=user_id,
        conv_id=conv_id,
    )

    # TODO: Update Team._teams with the new team for the user_id-conv_id pair

    team.initiate_chat()
    # the last message is TeamResponse in json encoded string
    last_message = team.get_last_message(add_prefix=False)
    return last_message


class Context(BaseModel):
    user_id: int
    conv_id: int


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
        "Get the brief template which will be used by the selected team"
    )
    def get_brief_template(
        team_name: Annotated[str, "The name of the team"],
    ) -> str:
        return _get_brief_template(team_name)

    @toolbox.add_function("Delagate the task to the selected team")
    def delagate_task(
        team_name: Annotated[str, "The name of the team"],
        task: Annotated[str, "The task to be delagated"],
        customers_brief: Annotated[str, "The brief from the customer"],
        context: Context,
    ) -> str:
        return _delagate_task(
            user_id=context.user_id,
            conv_id=context.conv_id,
            team_name=team_name,
            task=task,
            customers_brief=customers_brief,
        )

    return toolbox
