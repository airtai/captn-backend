from os import environ
from typing import Dict, List

from dotenv import load_dotenv
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

load_dotenv()

router = APIRouter()


class CaptnAgentRequest(BaseModel):
    conversation: List[Dict[str, str]]


async def _get_captn_response(conversation: List[Dict[str, str]]) -> str:
    try:
        async with httpx.AsyncClient() as client:
            # TODO: update the below
            response = await client.post(f"{environ.get('CAPTN_AGENT_URL')}/some-route", data="data")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post("/chat")
async def chat(request: CaptnAgentRequest) -> str:
    return await _get_captn_response(request.conversation)
