from typing import List, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from .utils import get_openai_response

router = APIRouter()


class AzureOpenAIRequest(BaseModel):
    conversation: List[Dict[str, str]]

@router.post("/chat")
async def create_item(request: AzureOpenAIRequest) -> str:
    conversation = request.conversation
    result = await get_openai_response(conversation)
    return result