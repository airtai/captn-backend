import inspect
from typing import List, Optional, Tuple
from unittest import mock

import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.tools._google_ads_team_tools import (
    create_google_ads_team_toolbox,
)
from google_ads.model import Campaign

from .helpers import check_llm_config_descriptions, check_llm_config_total_tools


class TestGoogleAdsTeamTools:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        user_id = 1234
        conv_id = 5678
        self.clients_question_answer_list: List[Tuple[str, Optional[str]]] = []

        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }

        self.toolbox = create_google_ads_team_toolbox(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answer_list=self.clients_question_answer_list,
        )

        self.agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        self.user_proxy = UserProxyAgent(name="user_proxy")

        self.toolbox.add_to_agent(self.agent, self.user_proxy)

    def test_llm_config(self) -> None:
        llm_config = self.agent.llm_config

        check_llm_config_total_tools(llm_config, 7)

        name_desc_dict = {
            "get_info_from_the_web_page": "Retrieve wanted information from the web page.",
            "reply_to_client_2": r"Respond to the client \(answer to his task or question for additional information\)",
            "ask_client_for_permission": "Ask the client for permission to make the changes.",
            "change_google_account": "This method should be used only when the client explicitly asks for the change of the Google account",
            "list_accessible_customers": "List all the customers accessible to the user",
            "execute_query": "Query the Google Ads API.",
            "create_campaign": "Creates Google Ads Campaign. VERY IMPORTANT:",
        }
        check_llm_config_descriptions(llm_config, name_desc_dict)

    def test_create_campaign_signature(self) -> None:
        create_campaign = self.user_proxy.function_map["create_campaign"]

        sig = inspect.signature(create_campaign)

        params = list(sig.parameters.values())

        names = [param.name for param in params]
        expected = [
            "customer_id",
            "name",
            "budget_amount_micros",
            "clients_approval_message",
            "modification_question",
            "status",
            "network_settings_target_google_search",
            "network_settings_target_search_network",
            "network_settings_target_content_network",
            "local_currency",
        ]
        assert set(names) == set(expected)

    def test_create_campaign_function(self) -> None:
        create_campaign = self.user_proxy.function_map["create_campaign"]

        with (
            mock.patch(
                "captn.captn_agents.backend.tools._google_ads_team_tools.google_ads_create_update",
                return_value="campaign created",
            ) as mock_google_ads_create_update,
            mock.patch(
                "captn.captn_agents.backend.tools._google_ads_team_tools._get_customer_currency",
                return_value="EUR",
            ) as mock_get_customer_currency,
        ):
            self.clients_question_answer_list.append(("whatsup?", "whatsup!"))

            create_campaign(
                customer_id="123",
                name="cool campaign",
                budget_amount_micros=1000,
                clients_approval_message="yes",
                modification_question="may I?",
                status="ENABLED",
                network_settings_target_google_search=True,
                network_settings_target_search_network=False,
                network_settings_target_content_network=True,
                local_currency="EUR",
            )

            mock_google_ads_create_update.assert_called_once_with(
                user_id=1234,
                conv_id=5678,
                clients_question_answer_list=[("whatsup?", "whatsup!")],
                clients_approval_message="yes",
                modification_question="may I?",
                ad=Campaign(
                    customer_id="123",
                    name="cool campaign",
                    budget_amount_micros=1000,
                    status="ENABLED",
                    network_settings_target_google_search=True,
                    network_settings_target_search_network=False,
                    network_settings_target_content_network=True,
                ),
                endpoint="/create-campaign",
            )

            mock_get_customer_currency.assert_called_once_with(
                user_id=1234, conv_id=5678, customer_id="123"
            )
            mock_get_customer_currency.reset_mock()

            with pytest.raises(
                ValueError,
                match=r"Error: Customer .+ account has set currency .EUR. which is different from the provided currency .+USD",
            ):
                create_campaign(
                    customer_id="987",
                    name="cool campaign",
                    budget_amount_micros=1000,
                    clients_approval_message="yes",
                    modification_question="may I?",
                    status="ENABLED",
                    network_settings_target_google_search=True,
                    network_settings_target_search_network=False,
                    network_settings_target_content_network=True,
                    local_currency="USD",
                )
            mock_get_customer_currency.assert_called_once_with(
                user_id=1234, conv_id=5678, customer_id="987"
            )

    def test_create_campaign_config(self) -> None:
        names = [
            function_wrapper["function"]["name"]
            for function_wrapper in self.agent.llm_config["tools"]
        ]
        i = names.index("create_campaign")
        create_campaign_config = self.agent.llm_config["tools"][i]["function"]
        assert create_campaign_config["name"] == "create_campaign"

        param_names = list(create_campaign_config["parameters"]["properties"].keys())

        assert "context" not in param_names

        expected = [
            "customer_id",
            "name",
            "budget_amount_micros",
            "clients_approval_message",
            "modification_question",
            "status",
            "network_settings_target_google_search",
            "network_settings_target_search_network",
            "network_settings_target_content_network",
            "local_currency",
        ]
        assert set(param_names) == set(expected)
