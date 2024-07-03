from typing import Iterator

import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.teams._team import Team
from captn.captn_agents.backend.tools._gbb_initial_team_tools import (
    create_gbb_initial_team_toolbox,
)

from .helpers import check_llm_config_descriptions, check_llm_config_total_tools


class TestTools:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }

        self.toolbox = create_gbb_initial_team_toolbox(
            user_id=12345,
            conv_id=67890,
            initial_brief="Initial brief. This is a test.",
        )

        yield
        Team._teams.clear()

    def test_llm_config(self) -> None:
        agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        user_proxy = UserProxyAgent(name="user_proxy", code_execution_config=False)

        self.toolbox.add_to_agent(agent, user_proxy)

        llm_config = agent.llm_config
        name_desc_dict = {
            "get_brief_template": "Get the TEMPLATE for the customer brief you will need to create",
            "delagate_task": "Delegate the task to the selected team",
            "reply_to_client": "Respond to the client",
        }

        check_llm_config_total_tools(llm_config, 3)
        check_llm_config_descriptions(llm_config, name_desc_dict)
