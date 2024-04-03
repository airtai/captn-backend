import unittest
from typing import Any, Dict

import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.teams._google_ads_team import GoogleAdsTeam
from captn.captn_agents.backend.teams._team import Team
from captn.captn_agents.backend.tools._brief_creation_team_tools import (
    Context,
    create_brief_creation_team_toolbox,
)
from captn.captn_agents.backend.tools._functions import TeamResponse

BRIEF_CREATION_TEAM_RESPONSE = r"""{"message":"Here is the list of all customer IDs accessible to you:\n- 7119828439\n- 7587037554","smart_suggestions":{"suggestions":[""],"type":""},"is_question":true,"status":"completed","terminate_groupchat":true}"""


class TestTools:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }

        self.toolbox = create_brief_creation_team_toolbox(
            user_id=12345,
            conv_id=67890,
        )

    def test_llm_config(self) -> None:
        def _check_llm_config(
            llm_config: Dict[str, Any], name_desc_dict: Dict[str, str]
        ) -> None:
            assert "tools" in llm_config, f"{llm_config.keys()=}"
            assert len(llm_config["tools"]) == 4, f"{llm_config['tools']=}"
            assert (
                llm_config["tools"][0]["type"] == "function"
            ), f"{llm_config['tools'][0]['type']=}"

            for i, (name, desc) in enumerate(name_desc_dict.items()):
                function_config = llm_config["tools"][i]["function"]

                assert function_config["name"] == name, function_config
                assert function_config["description"] == desc, function_config[
                    "description"
                ]

        agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        user_proxy = UserProxyAgent(name="user_proxy")

        self.toolbox.add_to_agent(agent, user_proxy)

        llm_config = agent.llm_config
        name_desc_dict = {
            "get_brief_template": "Get the TEMPLATE for the customer brief you will need to create",
            "delagate_task": "Delagate the task to the selected team",
        }
        _check_llm_config(llm_config, name_desc_dict)

    def test_delagate_task(self) -> None:
        agent = AssistantAgent(name="agent", llm_config=self.llm_config)

        self.toolbox.add_to_agent(agent, agent)

        # patch Team.initiate_chat and get_last_message
        with unittest.mock.patch(
            "captn.captn_agents.backend.teams._team.Team.initiate_chat"
        ) as mock_initiate_chat, unittest.mock.patch(
            "captn.captn_agents.backend.teams._team.Team.get_last_message"
        ) as mock_get_last_message:
            mock_initiate_chat.return_value = None
            mock_get_last_message.return_value = BRIEF_CREATION_TEAM_RESPONSE

            try:
                context = Context(
                    user_id=12345,
                    conv_id=67890,
                )

                delagate_task_f = self.toolbox.get_function("delagate_task")
                response = delagate_task_f(
                    team_name="default_team",
                    task="Just give me a list of all the customer ids.",
                    customers_brief="No brief",
                    summary_from_web_page="Summary from web page",
                    context=context,
                )

                team_response = TeamResponse.model_validate_json(response)
                print(f"team_response: {team_response}")
            finally:
                poped_team = Team.pop_team(user_id=12345, conv_id=67890)
                assert isinstance(poped_team, GoogleAdsTeam)
