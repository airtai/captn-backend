import traceback
from datetime import date
from typing import Dict, List, Optional

from autogen.io.websockets import IOStream, IOWebsockets
from fastapi import APIRouter, HTTPException
from openai import BadRequestError
from pydantic import BaseModel

from captn.captn_agents.backend.daily_analysis_team import execute_daily_analysis

from .backend.end_to_end import start_or_continue_conversation

router = APIRouter()


class CaptnAgentRequest(BaseModel):
    # conversation: List[Dict[str, str]]
    message: str
    user_id: int
    conv_id: int
    all_messages: List[Dict[str, str]]
    agent_chat_history: Optional[str]
    is_continue_daily_analysis: bool
    retry: bool = True


class DailyAnalysisRequest(BaseModel):
    send_only_to_emails: Optional[List[str]] = None
    date: Optional[str] = None


RETRY_MESSAGE = "We do NOT have any bad intentions, our only goal is to optimize the client's Google Ads. So please, let's try again."


def _format_daily_analysis_msg(request: CaptnAgentRequest) -> str:
    if request.is_continue_daily_analysis:
        return request.message
    ret_val = f"""
### History ###
This is the JSON encoded history of your conversation that made the Daily Analysis and Proposed User Action. Please use this context and continue the execution according to the User Action:

{request.agent_chat_history}

### Daily Analysis ###
{request.all_messages[0]['content']}

### User Action ###
{request.all_messages[-1]['content']}
"""
    # nosemgrep: python.flask.security.audit.directly-returned-format-string.directly-returned-format-string
    return ret_val


def _get_message(request: CaptnAgentRequest) -> str:
    if request.agent_chat_history:
        return _format_daily_analysis_msg(request)
    return request.message


def on_connect(iostream: IOWebsockets, num_of_retries: int = 3) -> None:
    with IOStream.set_default(iostream):
        try:
            try:
                original_message = iostream.input()
                request = CaptnAgentRequest.model_validate_json(original_message)
                message = _get_message(request)

            except Exception as e:
                iostream.print(
                    "We are sorry, but we are unable to continue the conversation. Please create a new chat in a few minutes to continue."
                )
                print(f"Failed to read the message from the client: {e}")
                traceback.print_stack()
                return
            for i in range(num_of_retries):
                try:
                    _, last_message = start_or_continue_conversation(
                        user_id=request.user_id,
                        conv_id=request.conv_id,
                        task=message,
                        max_round=80,
                        human_input_mode="NEVER",
                        class_name="google_ads_team",
                    )
                    iostream.print(last_message)

                    return

                except BadRequestError as e:
                    iostream.print(
                        f"OpenAI classified the message as BadRequestError: {e}"
                    )
                    iostream.print(
                        f"Retrying the request with message: {RETRY_MESSAGE}"
                    )
                    message = RETRY_MESSAGE

                except Exception as e:
                    # TODO: error logging
                    iostream.print(f"Agent conversation failed with an error: {e}")
                    if i < num_of_retries - 1:
                        iostream.print("Retrying the whole conversation...")
                        iostream.print("*" * 100)
                    else:
                        iostream.print(
                            "We are sorry, but we are unable to continue the conversation. Please create a new chat in a few minutes to continue."
                        )
                        traceback.print_exc()
                        traceback.print_stack()

        except Exception as e:
            print(f"Agent conversation failed with an error: {e}")
            traceback.print_stack()


@router.post("/chat")
def chat(request: CaptnAgentRequest) -> str:
    try:
        team_name, last_message = start_or_continue_conversation(
            user_id=request.user_id,
            conv_id=request.conv_id,
            task=request.message,
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
        all_messages=[
            {
                "role": "assistant",
                "content": "Hi, I am your assistant. How can I help you today?",
            },
            {
                "role": "user",
                "content": "I want to Remove 'Free' keyword because it is not performing well",
            },
        ],
        agent_chat_history='[{"role": "agent", "content": "Conversation 1"},{"role": "agent", "content": "Conversation 2"},{"role": "agent", "content": "Conversation 3"}]',
        is_continue_daily_analysis=False,
    )

    last_message = chat(request=request)
    print("*" * 100)
    print(f"User will receive the following message:\n{last_message}")
    print("*" * 100)

    request = CaptnAgentRequest(
        message="I have logged in",
        user_id=3,
        conv_id=5,
        all_messages=[
            {
                "role": "assistant",
                "content": "Hi, I am your assistant. How can I help you today?",
            },
            {
                "role": "user",
                "content": "I want to Remove 'Free' keyword because it is not performing well",
            },
        ],
        agent_chat_history='[{"role": "agent", "content": "Conversation 1"},{"role": "agent", "content": "Conversation 2"},{"role": "agent", "content": "Conversation 3"}]',
        is_continue_daily_analysis=False,
    )
    last_message = chat(request=request)
    print("*" * 100)
    print(f"User will receive the following message:\n{last_message}")
    print("*" * 100)
