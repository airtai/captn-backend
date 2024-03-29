from typing import Callable, Optional, Type

from autogen.agentchat import AssistantAgent, ConversableAgent
from typing_extensions import Annotated

from ..teams._team import Team


def add_get_brief_template(
    *,
    agent: AssistantAgent,
    executor: Optional[ConversableAgent] = None,
) -> Callable[..., str]:
    if executor is None:
        executor = agent

    @executor.register_for_execution()  # type: ignore[misc]
    @agent.register_for_llm(  # type: ignore[misc]
        name="get_brief_template",
        description="Get the brief template which will be used by the selected team",
    )
    def _get_brief_template(
        team_name: Annotated[str, "The name of the team"],
    ) -> str:
        team_class: Type[Team] = Team.get_class_by_name(team_name)
        return team_class.get_brief_template()

    return _get_brief_template  # type: ignore


def delagate_task(
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


def add_delagate_task(
    *,
    agent: AssistantAgent,
    executor: Optional[ConversableAgent] = None,
    user_id: int,
    conv_id: int,
) -> Callable[..., str]:
    if executor is None:
        executor = agent

    @executor.register_for_execution()  # type: ignore[misc]
    @agent.register_for_llm(  # type: ignore[misc]
        name="delagate_task",
        description="Delagate the task to the selected team",
    )
    def _delagate_task(
        team_name: Annotated[str, "The name of the team"],
        task: Annotated[str, "The task to be delagated"],
        customers_brief: Annotated[str, "The brief from the customer"],
    ) -> str:
        return delagate_task(
            user_id=user_id,
            conv_id=conv_id,
            team_name=team_name,
            task=task,
            customers_brief=customers_brief,
        )

    return _delagate_task  # type: ignore
