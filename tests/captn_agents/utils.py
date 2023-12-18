from captn.captn_agents.backend.google_ads_team import GoogleAdsTeam
from captn.captn_agents.backend.team import Team


def last_message_is_termination(team: Team, is_gads_team: bool = False) -> bool:
    last_message = team.groupchat.messages[-1]
    # last_message = team.manager.chat_messages[team.members[0]][-1]
    if is_gads_team:
        return GoogleAdsTeam._is_termination_msg(last_message)
    return Team._is_termination_msg(last_message)
