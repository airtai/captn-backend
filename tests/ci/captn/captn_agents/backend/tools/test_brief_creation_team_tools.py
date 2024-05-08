import unittest
from typing import Optional

import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent

from captn.captn_agents.backend.benchmarking.fixtures.brief_creation_team_fixtures import (
    BRIEF_CREATION_TEAM_RESPONSE,
)
from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.teams._google_ads_team import GoogleAdsTeam
from captn.captn_agents.backend.teams._team import Team
from captn.captn_agents.backend.tools._brief_creation_team_tools import (
    Context,
    DelegateTask,
    create_brief_creation_team_toolbox,
)
from captn.captn_agents.backend.tools._functions import TeamResponse

from .helpers import check_llm_config_descriptions, check_llm_config_total_tools


class TestTools:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }

        self.toolbox = create_brief_creation_team_toolbox(
            user_id=12345,
            conv_id=67890,
            initial_brief="Initial brief. This is a test.",
        )

    def test_llm_config(self) -> None:
        agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        user_proxy = UserProxyAgent(name="user_proxy")

        self.toolbox.add_to_agent(agent, user_proxy)

        llm_config = agent.llm_config
        name_desc_dict = {
            "get_brief_template": "Get the TEMPLATE for the customer brief you will need to create",
            "delagate_task": "Delegate the task to the selected team",
        }

        check_llm_config_total_tools(llm_config, 4)
        check_llm_config_descriptions(llm_config, name_desc_dict)

    @pytest.mark.parametrize(
        "get_info_from_web_page_result",
        [
            "My web page info.",
            None,
        ],
    )
    def test_delagate_task(self, get_info_from_web_page_result: Optional[str]) -> None:
        agent = AssistantAgent(name="agent", llm_config=self.llm_config)

        self.toolbox.add_to_agent(agent, agent)

        with (
            unittest.mock.patch(
                "captn.captn_agents.backend.teams._team.Team.initiate_chat"
            ) as mock_initiate_chat,
            unittest.mock.patch(
                "captn.captn_agents.backend.teams._team.Team.get_last_message"
            ) as mock_get_last_message,
        ):
            mock_initiate_chat.return_value = None
            mock_get_last_message.return_value = BRIEF_CREATION_TEAM_RESPONSE

            try:
                context = Context(
                    user_id=12345,
                    conv_id=67890,
                    initial_brief="Initial brief. This is a test.",
                    get_info_from_web_page_result=get_info_from_web_page_result,
                )

                delagate_task_f = self.toolbox.get_function("delagate_task")
                task_and_context_to_delegate = DelegateTask(
                    team_name="default_team",
                    task="Just give me a list of all the customer ids.",
                    customers_business_brief="Customer business brief, at least 30 char. This is a test.",
                )
                response = delagate_task_f(
                    task_and_context_to_delegate=task_and_context_to_delegate,
                    context=context,
                )

                if get_info_from_web_page_result is None:
                    assert isinstance(response, str)
                    mock_initiate_chat.assert_not_called()
                    mock_get_last_message.assert_not_called()
                else:
                    mock_initiate_chat.assert_called()
                    mock_get_last_message.assert_called()
                    team_response = TeamResponse.model_validate_json(response)
                    print(f"team_response: {team_response}")
            finally:
                if get_info_from_web_page_result is not None:
                    poped_team = Team.pop_team(user_id=12345, conv_id=67890)
                    assert isinstance(poped_team, GoogleAdsTeam)
