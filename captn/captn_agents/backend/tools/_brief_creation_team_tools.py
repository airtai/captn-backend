from typing import Type

from pydantic import BaseModel
from typing_extensions import Annotated

from ..teams._team import Team
from ..toolboxes import Toolbox
from ._functions import (
    get_info_from_the_web_page,
    reply_to_client_2,
    reply_to_client_2_description,
)


def _get_brief_template(
    team_name: str,
) -> str:
    team_class: Type[Team] = Team.get_class_by_registred_team_name(team_name)
    return team_class.get_brief_template()


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
        "Get the TEMPLATE for the customer brief you will need to create"
    )
    def get_brief_template(
        team_name: Annotated[str, "The name of the team"],
    ) -> str:
        team_class: Type[Team] = Team.get_class_by_registred_team_name(team_name)
        return team_class.get_brief_template()

    @toolbox.add_function("Delagate the task to the selected team")
    def delagate_task(
        team_name: Annotated[str, "The name of the team"],
        task: Annotated[str, "The task to be delagated"],
        customers_brief: Annotated[str, "The brief from the customer"],
        summary_from_web_page: Annotated[str, "The summary of the web page content"],
        context: Context,
    ) -> str:
        user_id = context.user_id
        conv_id = context.conv_id

        team_class: Type[Team] = Team.get_class_by_registred_team_name(team_name)

        final_task = f"Here is the customer brief:\n{customers_brief}\n\nAdditional info from the web page:\n{summary_from_web_page}\n\nAnd the task is following:\n{task}"

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

    get_info_from_the_web_page_desc = """Retrieve wanted information from the web page.
There is no need to test this function (by sending url: https://www.example.com).
NEVER use this function for scraping Google Ads pages (e.g. https://ads.google.com/aw/campaigns?campaignId=1212121212)
"""

    toolbox.add_function(get_info_from_the_web_page_desc)(get_info_from_the_web_page)

    toolbox.add_function(reply_to_client_2_description)(reply_to_client_2)

    return toolbox
