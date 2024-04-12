from captn.captn_agents.backend.teams._google_ads_team import GoogleAdsTeam

from .helpers import helper_test_init


class TestGoogleAdsTeam:
    def test_init(self) -> None:
        google_ads_team = GoogleAdsTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )

        helper_test_init(
            team=google_ads_team,
            number_of_team_members=5,
            number_of_functions=21,
            team_class=GoogleAdsTeam,
        )
