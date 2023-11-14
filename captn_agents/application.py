from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from captn_agents.end_to_end import start_conversation

router = APIRouter()


class AzureOpenAIRequest(BaseModel):
    # conversation: List[Dict[str, str]]
    message: str
    user_id: int
    conv_id: int


@router.post("/chat")
def chat(request: AzureOpenAIRequest) -> str:
    team_name, last_message = start_conversation(
        user_id=request.user_id,
        conv_id=request.conv_id,
        task=request.message,
        max_round=80,
        human_input_mode="NEVER",
        class_name="captn_initial_team",
    )

    return last_message


if __name__ == "__main__":
    request = AzureOpenAIRequest(
        message = "What are the metods for campaign optimization",
        user_id = 3,
        conv_id = 5,
    )

    last_message = chat(request=request)
    print("*"*100)
    print(f"User will receive the following message:\n{last_message}")
    print("*"*100)


    request = AzureOpenAIRequest(
        message = "I have logged in",
        user_id = 3,
        conv_id = 5,
    )
    last_message = chat(request=request)
    print("*"*100)
    print(f"User will receive the following message:\n{last_message}")
    print("*"*100)
