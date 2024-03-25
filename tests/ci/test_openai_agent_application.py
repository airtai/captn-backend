import pytest

from openai_agent.application import offload_work_to_google_ads_expert


@pytest.mark.asyncio
async def test_offload_work_to_google_ads_expert() -> None:
    response = await offload_work_to_google_ads_expert(
        user_id=1,
        chat_id=2,
        customer_brief="This is a test content",
        google_ads_team="default_team",
    )
    assert response["team_name"] == "google_ads_team_1_2"

    response = await offload_work_to_google_ads_expert(
        user_id=1,
        chat_id=2,
        customer_brief="This is a test content",
        google_ads_team="campaign_creation_team",
    )
    assert response["team_name"] == "campaign_creation_team_1_2"
