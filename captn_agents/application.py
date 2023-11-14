import json
from os import environ
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

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
        use_captn_class=True,
    )

    return team_name, last_message


if __name__ == "__main__":
    request = AzureOpenAIRequest(
        message = "What are the metods for campaign optimization",
        user_id = 3,
        conv_id = 5,
    )

    chat(request=request)
