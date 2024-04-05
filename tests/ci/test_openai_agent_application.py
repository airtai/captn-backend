import pytest

from openai_agent.application import offload_work_to_google_ads_expert


@pytest.mark.asyncio
async def test_offload_work_to_google_ads_expert() -> None:
    response = await offload_work_to_google_ads_expert(
        user_id=1,
        chat_id=2,
        customer_brief="This is a test content",
        conversation_name="My conversation"
    )
    assert response["team_name"] == "brief_creation_team"
