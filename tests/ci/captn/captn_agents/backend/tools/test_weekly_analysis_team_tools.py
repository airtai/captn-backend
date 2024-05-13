from typing import List, Optional, Tuple

import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.tools._weekly_analysis_team_tools import (
    create_weekly_analysis_team_toolbox,
)

from .helpers import check_llm_config_descriptions, check_llm_config_total_tools


class TestWeeklyAnalysisTeamTools:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        user_id = 1234
        conv_id = 5678
        self.clients_question_answer_list: List[Tuple[str, Optional[str]]] = []

        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }

        self.toolbox = create_weekly_analysis_team_toolbox(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answer_list=self.clients_question_answer_list,
        )

        self.agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        self.user_proxy = UserProxyAgent(name="user_proxy")

        self.toolbox.add_to_agent(self.agent, self.user_proxy)

    def test_llm_config(self) -> None:
        llm_config = self.agent.llm_config

        check_llm_config_total_tools(llm_config, 4)

        name_desc_dict = {
            "list_accessible_customers": "List all the customers accessible to the user",
            "execute_query": "Query the Google Ads API.",
            "get_info_from_the_web_page": "Retrieve wanted information from the web page.",
            "send_email": "Send email to the client.",
        }
        check_llm_config_descriptions(llm_config, name_desc_dict)
