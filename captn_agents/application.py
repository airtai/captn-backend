from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .captn_agents.end_to_end import start_conversation

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
        class_name="banking_initial_team",
    )

    return last_message


if __name__ == "__main__":
    request = CaptnAgentRequest(
        message = "I need a loan for 100,000 euros for a period of 10 years. Please provide me the credit calculation",
        user_id = 3,
        conv_id = 5,
    )

    last_message = chat(request=request)
    print("*"*100)
    print(f"User will receive the following message:\n{last_message}")
    print("*"*100)


    request = CaptnAgentRequest(
        message = "I don't have any previous loans or credit history.",
        user_id = 3,
        conv_id = 5,
    )
    last_message = chat(request=request)
    print("*"*100)
    print(f"User will receive the following message:\n{last_message}")
    print("*"*100)
