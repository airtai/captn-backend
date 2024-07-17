import unittest

import prisma
import pytest
from fastapi.testclient import TestClient

from openai_agent.application import (
    AzureOpenAIRequest,
    offload_work_to_google_ads_expert,
    router,
)


@pytest.mark.asyncio
async def test_offload_work_to_google_ads_expert() -> None:
    response = await offload_work_to_google_ads_expert(
        user_id=1,
        chat_id=2,
        customer_brief="This is a test content",
        conversation_name="My conversation",
    )
    assert response["team_name"] == "brief_creation_team"


class TestChat:
    def test_chat(self) -> None:
        client = TestClient(router)
        request = AzureOpenAIRequest(
            user_id=123, chat_id=234, message=[{"role": "user", "content": "Hello"}]
        )

        with unittest.mock.patch(
            "openai_agent.application.get_initial_team"
        ) as mock_get_user_initial_team:
            initial_team = prisma.models.InitialTeam(
                id=1, name="test_team", smart_suggestions=["test suggestion"]
            )
            user_initial_team = prisma.models.UserInitialTeam(
                id=1, user_id=123, initial_team_id=1, initial_team=initial_team
            )
            mock_get_user_initial_team.return_value = user_initial_team

            response = client.post("/chat", json=request.model_dump())

            assert response.status_code == 200
            expected = {
                "team_status": "inprogress",
                "team_name": "test_team",
                "team_id": 234,
                "customer_brief": "Hello",
                "conversation_name": "Team of Experts",
            }
            assert response.json() == expected
