import traceback
from datetime import date
from pathlib import Path
from typing import Annotated, Dict, List, Literal, Optional, TypeVar, Union

import aiofiles
import httpx
import openai
import pandas as pd
from autogen.io.websockets import IOWebsockets
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from prometheus_client import Counter
from pydantic import BaseModel

from ..observability.websocket_utils import (
    PING_REQUESTS,
    WEBSOCKET_REQUESTS,
    WEBSOCKET_TOKENS,
)
from .backend import Team, execute_weekly_analysis, start_or_continue_conversation

router = APIRouter()

google_ads_team_names = Team.get_registred_team_names()
TeamNames = TypeVar("TeamNames", bound=Literal[tuple(google_ads_team_names)])  # type: ignore[misc]

THREE_IN_A_ROW_EXCEPTIONS = Counter(
    "three_in_a_row_exceptions_total",
    "Total count of three in a row exceptions",
)
REGULAR_EXCEPTIONS = Counter(
    "regular_exceptions_total", "Total count of regular exceptions"
)
INVALID_MESSAGE_IN_IOSTREAM = Counter(
    "invalid_message_in_iostream_total", "Total count of invalid messages in iostream"
)
RANDOM_EXCEPTIONS = Counter(
    "random_exceptions_total", "Total count of random exceptions"
)


class CaptnAgentRequest(BaseModel):
    # conversation: List[Dict[str, str]]
    message: str
    user_id: int
    conv_id: int
    google_ads_team: TeamNames = "default_team"  # type: ignore[valid-type]
    all_messages: List[Dict[str, str]]
    agent_chat_history: Optional[str]
    is_continue_daily_analysis: bool
    retry: bool = True


class WeeklyAnalysisRequest(BaseModel):
    send_only_to_emails: Optional[List[str]] = None
    date: Optional[str] = None


RETRY_MESSAGE = "We do NOT have any bad intentions, our only goal is to optimize the client's Google Ads. So please, let's try again."


def _format_weekly_analysis_msg(request: CaptnAgentRequest) -> str:
    if request.is_continue_daily_analysis:
        return request.message
    ret_val = f"""
### History ###
This is the JSON encoded history of your conversation that made the Weekly Analysis and Proposed User Action. Please use this context and continue the execution according to the User Action:

{request.agent_chat_history}

### Weekly Analysis ###
{request.all_messages[0]['content']}

### User Action ###
{request.all_messages[-1]['content']}
"""
    # nosemgrep: python.flask.security.audit.directly-returned-format-string.directly-returned-format-string
    return ret_val


def _get_message(request: CaptnAgentRequest) -> str:
    if request.agent_chat_history:
        return _format_weekly_analysis_msg(request)
    return request.message


ON_FAILURE_MESSAGE = "We are sorry, but we are unable to continue the conversation. Please create a new chat in a few minutes to continue."


def _handle_exception(
    iostream: IOWebsockets, num_of_retries: int, e: Exception, retry: int
) -> None:
    # TODO: error logging
    iostream.print(f"Agent conversation failed with an error: {e}")
    REGULAR_EXCEPTIONS.inc()
    if retry < num_of_retries - 1:
        iostream.print("Retrying the whole conversation...")
        iostream.print("*" * 100)
    else:
        THREE_IN_A_ROW_EXCEPTIONS.inc()
        iostream.print(ON_FAILURE_MESSAGE)
        traceback.print_exc()
        traceback.print_stack()


def on_connect(iostream: IOWebsockets, num_of_retries: int = 3) -> None:
    try:
        try:
            original_message = iostream.input()
            if original_message == "ping":
                PING_REQUESTS.inc()
                iostream.print("pong")
                return
            WEBSOCKET_REQUESTS.inc()
            request = CaptnAgentRequest.model_validate_json(original_message)
            message = _get_message(request)
            for i in range(num_of_retries):
                try:
                    registred_team_name = request.google_ads_team
                    _, last_message = start_or_continue_conversation(
                        user_id=request.user_id,
                        conv_id=request.conv_id,
                        task=message,
                        max_round=80,
                        registred_team_name=registred_team_name,
                    )
                    iostream.print(last_message)

                    return

                except (
                    openai.APIStatusError,
                    httpx.ReadTimeout,
                    openai.BadRequestError,
                    TimeoutError,
                ):
                    iostream.print(ON_FAILURE_MESSAGE)
                    THREE_IN_A_ROW_EXCEPTIONS.inc()
                    # Do NOT try to recover from these errors, it has already been tried in Team class
                    break

                except Exception as e:
                    _handle_exception(
                        iostream=iostream, num_of_retries=num_of_retries, e=e, retry=i
                    )

            # ToDo: fix this @rjambercic
            WEBSOCKET_TOKENS.inc(len(message.split()))
        except Exception as e:
            INVALID_MESSAGE_IN_IOSTREAM.inc()
            iostream.print(ON_FAILURE_MESSAGE)
            print(f"Failed to read the message from the client: {e}")
            traceback.print_stack()
            return

    except Exception as e:
        RANDOM_EXCEPTIONS.inc()
        print(f"Agent conversation failed with an error: {e}")
        traceback.print_stack()


@router.get("/weekly-analysis")
def weekly_analysis(request: WeeklyAnalysisRequest) -> str:
    if request.date is not None:
        try:
            date.fromisoformat(request.date)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Please use YYYY-MM-DD"
            ) from e

    execute_weekly_analysis(
        send_only_to_emails=request.send_only_to_emails, date=request.date
    )
    return "Weekly analysis has been sent to the specified emails"


AVALIABLE_FILE_CONTENT_TYPES = [
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]
MANDATORY_COLUMNS = {"from_destination", "to_destination"}

UPLOADED_FILES_DIR = Path(__file__).resolve().parent.parent.parent / "uploaded_files"


@router.post("/uploadfile/")
async def create_upload_file(
    file: Annotated[UploadFile, File()],
    user_id: Annotated[int, Form()],
    conv_id: Annotated[int, Form()],
) -> Dict[str, Union[str, None]]:
    if file.content_type not in AVALIABLE_FILE_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file content type: {file.content_type}. Only {', '.join(AVALIABLE_FILE_CONTENT_TYPES)} are allowed.",
        )
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Invalid file name")

    # Create a directory if not exists
    users_conv_dir = UPLOADED_FILES_DIR / str(user_id) / str(conv_id)
    users_conv_dir.mkdir(parents=True, exist_ok=True)
    file_path = users_conv_dir / file.filename

    # Async read-write
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    # Check if the file has mandatory columns
    if file.content_type == "text/csv":
        df = pd.read_csv(file_path, nrows=0)
    else:
        df = pd.read_excel(file_path, nrows=0)
    if not MANDATORY_COLUMNS.issubset(df.columns):
        # Remove the file
        file_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=f"Missing mandatory columns: {', '.join(MANDATORY_COLUMNS - set(df.columns))}",
        )

    return {"filename": file.filename}
