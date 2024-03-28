from captn.captn_agents.backend.teams import BriefCreationTeam, Team


def test_get_avaliable_teams_and_their_descriptions() -> None:
    avaliable_teams_and_their_descriptions = (
        BriefCreationTeam._get_avaliable_team_names_and_their_descriptions()
    )

    # All teams except the BriefCreationTeam should be in the dictionary
    assert len(avaliable_teams_and_their_descriptions) == len(Team._team_registry) - 1
