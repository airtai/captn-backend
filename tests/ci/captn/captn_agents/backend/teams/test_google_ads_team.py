from captn.captn_agents.backend.teams._google_ads_team import GoogleAdsTeam

from .helpers import helper_test_init


class TestGoogleAdsTeam:
    def test_init(self) -> None:
        google_ads_team = GoogleAdsTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )

        agent_number_of_functions_dict = {
            "google_ads_specialist": 21,
            "copywriter": 21,
            "digital_strategist": 21,
            "account_manager": 21,
            "user_proxy": 0,
        }

        helper_test_init(
            team=google_ads_team,
            number_of_registered_executions=21,
            agent_number_of_functions_dict=agent_number_of_functions_dict,
            team_class=GoogleAdsTeam,
        )
