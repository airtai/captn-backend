from fastapi import APIRouter
from pydantic import BaseModel

from .backend.end_to_end import start_conversation

router = APIRouter()


class CaptnAgentRequest(BaseModel):
    # conversation: List[Dict[str, str]]
    message: str
    user_id: int
    conv_id: int


@router.post("/chat")
def chat(request: CaptnAgentRequest) -> str:
    team_name, last_message = start_conversation(
        user_id=request.user_id,
        conv_id=request.conv_id,
        task=request.message,
        max_round=80,
        human_input_mode="NEVER",
        class_name="google_ads_team",
    )

    return last_message


if __name__ == "__main__":
    request = CaptnAgentRequest(
        message="What are the metods for campaign optimization",
        user_id=3,
        conv_id=5,
    )

    last_message = chat(request=request)
    print("*" * 100)
    print(f"User will receive the following message:\n{last_message}")
    print("*" * 100)

    request = CaptnAgentRequest(
        message="I have logged in",
        user_id=3,
        conv_id=5,
    )
    last_message = chat(request=request)
    print("*" * 100)
    print(f"User will receive the following message:\n{last_message}")
    print("*" * 100)
