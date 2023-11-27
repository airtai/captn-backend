import pytest

from captn.captn_agents.backend.end_to_end import start_conversation
from captn.captn_agents.backend.team import Team

from .utils import last_message_is_termination

# record the cassete (first time): pytest --record-mode=once test_captn_end_to_end.py -s


# cassettes/{module_name}/test_end_to_end.yaml will be used


def before_record_response(response):
    # do not record 429 and 500 responses
    # if ("status_code" in response) and (response["status_code"] in [429, 500]):
    #     return None
    # if ("status_code" in response) and (response["status_code"] in [429]):
    #     return None
    return response


@pytest.mark.vcr(
    filter_headers=["api-key", "X-OpenAI-Client-User-Agent"],
    before_record_response=before_record_response,
)
def test_end_to_end() -> None:
    task = "Please optimize my Google ads campaigns, but don't change the budget. Propose and implement any solution as long it is legal and doesn't change the budget."
    user_id = 1
    conv_id = 17

    # create_google_ads_team = get_create_google_ads_team(
    #     user_id=user_id, conv_id=conv_id, working_dir=working_dir
    # )
    # with mock.patch(
    #     "captn.captn_agents.captn_initial_team.get_create_google_ads_team",
    #     return_value=create_google_ads_team,
    # ) as mock_get_create_google_ads_team:
    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        max_round=80,
        human_input_mode="NEVER",
        class_name="captn_initial_team",
    )

    initial_team = Team.get_team(team_name)

    # HOW TO MOCK INNER FUNCTION: get_create_google_ads_team.create_google_ads_team ???
    # print(f"{mock_get_create_google_ads_team.call_args_list=}")
    # mock_get_create_google_ads_team.assert_called_once()
    assert last_message_is_termination(initial_team)

    start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task="I have authenticated",
        max_round=80,
        human_input_mode="NEVER",
        class_name="captn_initial_team",
    )

    start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task="I allow the mentioned changes.",
        max_round=80,
        human_input_mode="NEVER",
        class_name="captn_initial_team",
    )

    # continue_conversation(
    #     team_name=team_name,
    #     message="Please write a summary of what has been done",
    # )


def test_hello() -> None:
    task = "Hello"
    user_id = 1
    conv_id = 17

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        max_round=80,
        human_input_mode="NEVER",
        class_name="captn_initial_team",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team)


def test_non_relevant_questions() -> None:
    task = "Which city is the capital of Croatia?"
    user_id = 1
    conv_id = 17

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        max_round=80,
        human_input_mode="NEVER",
        class_name="captn_initial_team",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team)
