import random
from datetime import datetime

from captn.captn_agents.backend.daily_analysis_team import DailyAnalysisTeam
from captn.captn_agents.backend.team import Team
from captn.captn_agents.backend.daily_analysis_team import get_daily_report, DailyCampaignReport
import unittest.mock

from autogen.cache import Cache


def test_get_daily_report():
    with unittest.mock.patch("captn.captn_agents.backend.daily_analysis_team.get_campaign_ids") as mock_get_campaign_ids:
        with unittest.mock.patch("captn.captn_agents.backend.daily_analysis_team.get_daily_report_for_campaign") as mock_get_daily_report_for_campaign:
            with unittest.mock.patch("captn.captn_agents.backend.daily_analysis_team.list_accessible_customers") as mock_list_accessible_customers:
                mock_list_accessible_customers.return_value = ["1"]
                mock_get_campaign_ids.return_value = ["2"]
                mock_get_daily_report_for_campaign.return_value = DailyCampaignReport(
                    campaign_id="2",
                    campaign_name="Test Campaign",
                    impressions=100,
                    clicks=10,
                    interactions=5,
                    conversions=2,
                    cost_micros=1000000,
                    date="2021-01-01",
                )
                daily_report = get_daily_report(user_id=1, conv_id=1)
                
    expected = """{
  "daily_customer_reports": [
    {
      "customer_id": "1",
      "daily_campaign_reports": [
        {
          "campaign_id": "2",
          "campaign_name": "Test Campaign",
          "impressions": 100,
          "clicks": 10,
          "interactions": 5,
          "conversions": 2,
          "cost_micros": 1000000,
          "date": "2021-01-01"
        }
      ]
    }
  ]
}"""
    assert expected == daily_report
    print(daily_report)


def test_daily_analysis_team():
    current_date = datetime.today().strftime("%Y-%m-%d")
    # task = f"""
    # Current date is: {current_date}.
    # You need compare the campaign performance between today and the previous three days.
    # Check which campaigns have the highest cost and which have the highest number of conversions.
    # Focus only on campaigns which do NOT have status REMOVED."""

    task = f"""
    Current date is: {current_date}.
    You need compare the ads performance between today and the previous 30 days:
    - Total ad views
    - Total website visits
    - Total actions from ads

    Check which ads have the highest cost and which have the highest number of conversions.
    If for some reason thera are no recorded impressions/clicks/interactions/conversions for any of the ads across all campaigns try to identify the reason (bad positive/negative keywords etc).
    At the end of the analysis, you need to suggest the next steps to the client. Usually, the next steps are:
    - pause the ads with the highest cost and the lowest number of conversions.
    - keywords analysis (add negative keywords, add positive keywords, change match type etc).
    - ad copy analysis (change the ad copy, add more ads etc).
    """

    conv_id = random.randint(1, 100)
    daily_analysis_team = DailyAnalysisTeam(
        task=task,
        user_id=1,
        conv_id=conv_id,
    )

    with unittest.mock.patch("captn.captn_agents.backend.daily_analysis_team.get_campaign_ids") as mock_get_campaign_ids:
        with unittest.mock.patch("captn.captn_agents.backend.daily_analysis_team.get_daily_report_for_campaign") as mock_get_daily_report_for_campaign:
            with unittest.mock.patch("captn.captn_agents.backend.daily_analysis_team.list_accessible_customers") as mock_list_accessible_customers:
                with unittest.mock.patch("captn.captn_agents.backend.daily_analysis_team.datetime") as mock_datetime:
                
                    with Cache.disk(cache_seed=42):
                        mock_list_accessible_customers.return_value = ["1"]
                        mock_get_campaign_ids.return_value = ["2"]
                        mock_get_daily_report_for_campaign.return_value = DailyCampaignReport(
                            campaign_id="2",
                            campaign_name="Test Campaign",
                            impressions=100,
                            clicks=10,
                            interactions=5,
                            conversions=2,
                            cost_micros=1000000,
                            date="2021-01-01",
                        )
                        mock_datetime.today.return_value = datetime(2021, 1, 1)

                        daily_analysis_team.initiate_chat()
    mock_list_accessible_customers.assert_called_once_with(user_id=1, conv_id=conv_id)
    mock_get_campaign_ids.assert_called_once_with(customer_id="1")

    
    mock_get_daily_report_for_campaign.assert_called_once_with(campaign_id="2", date="2021-01-01")



    team_name = daily_analysis_team.name
    print(team_name)
    last_message = daily_analysis_team.get_last_message(add_prefix=False)
    Team.pop_team(team_name=team_name)
