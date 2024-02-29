from datetime import date
from typing import List, Optional

from autogen.io.websockets import IOWebsockets
from fastapi import APIRouter, HTTPException
from openai import BadRequestError
from pydantic import BaseModel

from captn.captn_agents.backend.daily_analysis_team import execute_daily_analysis

from .backend.end_to_end import start_conversation

router = APIRouter()


class CaptnAgentRequest(BaseModel):
    # conversation: List[Dict[str, str]]
    message: str
    user_id: int
    conv_id: int
    retry: bool = True


class DailyAnalysisRequest(BaseModel):
    send_only_to_emails: Optional[List[str]] = None
    date: Optional[str] = None


RETRY_MESSAGE = "We do NOT have any bad intentions, our only goal is to optimize the client's Google Ads. So please, let's try again."


def on_connect(iostream: IOWebsockets) -> None:
    try:
        message = iostream.input()
        request_json = message
        request = CaptnAgentRequest.model_validate_json(request_json)
        print("===============================================")
        print(f"Received request: {request}", flush=True)

        start_conversation(
            user_id=request.user_id,
            conv_id=request.conv_id,
            task=request.message,
            iostream=iostream,
            max_round=80,
            human_input_mode="NEVER",
            class_name="google_ads_team",
        )

    except BadRequestError as e:
        # retry the request once
        if request.retry:
            request.retry = False
            request.message = RETRY_MESSAGE
            print(f"Retrying the request with message: {RETRY_MESSAGE}, error: {e}")

            # TODO: after updating request.retry, iostream should be updated as well?
            # And call on_connect again
            on_connect(iostream)
        raise e

    except Exception as e:
        # TODO: error logging
        print(f"captn_agents endpoint /chat failed with error: {e}")
        raise e


@router.post("/chat")
def chat(request: CaptnAgentRequest) -> str:
    try:
        team_name, last_message = start_conversation(
            user_id=request.user_id,
            conv_id=request.conv_id,
            task=request.message,
            iostream=None,
            max_round=80,
            human_input_mode="NEVER",
            class_name="google_ads_team",
        )

    except BadRequestError as e:
        # retry the request once
        if request.retry:
            request.retry = False
            request.message = RETRY_MESSAGE
            print(f"Retrying the request with message: {RETRY_MESSAGE}, error: {e}")
            return chat(request)
        raise e

    except Exception as e:
        # TODO: error logging
        print(f"captn_agents endpoint /chat failed with error: {e}")
        raise e

    return last_message


@router.get("/daily-analysis")
def daily_analysis(request: DailyAnalysisRequest) -> str:
    if request.date is not None:
        try:
            date.fromisoformat(request.date)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Please use YYYY-MM-DD"
            ) from e

    execute_daily_analysis(
        send_only_to_emails=request.send_only_to_emails, date=request.date
    )
    return "Daily analysis has been sent to the specified emails"


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
