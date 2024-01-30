import random
from datetime import datetime

from captn.captn_agents.backend.daily_analysis_team import DailyAnalysisTeam
from captn.captn_agents.backend.team import Team

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

daily_analysis_team.initiate_chat()

team_name = daily_analysis_team.name
print(team_name)
last_message = daily_analysis_team.get_last_message(add_prefix=False)
Team.pop_team(team_name=team_name)
