from captn_agents.team import Team


def last_message_is_termination(team: Team) -> bool:
    last_message = team.manager.chat_messages[team.members[0]][-1]
    return Team._is_termination_msg(last_message)
