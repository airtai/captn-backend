from typing import List, Optional, Tuple

import pytest
from pydantic import BaseModel

from captn.google_ads.client import (
    FIELDS_ARE_NOT_MENTIONED_ERROR_MSG,
    NOT_APPROVED,
    NOT_IN_QUESTION_ANSWER_LIST,
    _check_for_client_approval,
    check_fields_are_mentioned_to_the_client,
    clean_error_response,
    google_ads_create_update,
)


def test_clean_error_response() -> None:
    content = b'{"detail":"(<_InactiveRpcError of RPC that terminated with:\\n\\tstatus = StatusCode.INVALID_ARGUMENT\\n\\tdetails = \\"Request contains an invalid argument.\\"\\n\\tdebug_error_string = \\"UNKNOWN:Error received from peer ipv4:142.250.184.138:443 {created_time:\\"2024-01-31T10:13:18.977793+01:00\\", grpc_status:3, grpc_message:\\"Request contains an invalid argument.\\"}\\"\\n>, <_InactiveRpcError of RPC that terminated with:\\n\\tstatus = StatusCode.INVALID_ARGUMENT\\n\\tdetails = \\"Request contains an invalid argument.\\"\\n\\tdebug_error_string = \\"UNKNOWN:Error received from peer ipv4:142.250.184.138:443 {created_time:\\"2024-01-31T10:13:18.977793+01:00\\", grpc_status:3, grpc_message:\\"Request contains an invalid argument.\\"}\\"\\n>, errors {\\n  error_code {\\n    query_error: PROHIBITED_RESOURCE_TYPE_IN_SELECT_CLAUSE\\n  }\\n  message: \\"Cannot select fields from the following resources: \\\\\'AD_GROUP_CRITERION\\\\\', \\\\\'AD_GROUP\\\\\', since the resource is incompatible with the resource in FROM clause.\\"\\n}\\nrequest_id: \\"-3cDGJ1vaY4dJymqB5Ylag\\"\\n, \'-3cDGJ1vaY4dJymqB5Ylag\')"}'
    expected = "  message: \"Cannot select fields from the following resources: \\'AD_GROUP_CRITERION\\', \\'AD_GROUP\\', since the resource is incompatible with the resource in FROM clause.\""

    assert clean_error_response(content) == expected


def test_check_for_client_approval() -> None:
    error_msg = _check_for_client_approval(
        error_msg="",
        clients_approval_message="yes ",
        modification_question="modification_question",
        clients_question_answere_list=[("modification_question", "yes ")],
    )
    assert error_msg == ""


def test_check_for_client_approval_not_in_qa_list() -> None:
    error_msg = _check_for_client_approval(
        error_msg="",
        clients_approval_message="yes",
        modification_question="modification_question",
        clients_question_answere_list=[("aa", "bb")],
    )
    assert error_msg.strip() == NOT_IN_QUESTION_ANSWER_LIST


def test_check_for_client_approval_client_did_not_approve() -> None:
    error_msg = _check_for_client_approval(
        error_msg="",
        clients_approval_message="yes 123",
        modification_question="modification_question",
        clients_question_answere_list=[("modification_question", "yes 123")],
    )
    assert error_msg.strip() == NOT_APPROVED


class AdTest(BaseModel):
    ad_id: Optional[int] = None
    ad_name: str
    status: str


def test_check_fields_are_mentioned_to_the_client_returns_error_msg() -> None:
    modification_question = "Do you approve changing the ad_name to test?"
    ad = AdTest(ad_name="test", status="enabled")
    error_msg = check_fields_are_mentioned_to_the_client(ad, modification_question)
    assert error_msg == (
        FIELDS_ARE_NOT_MENTIONED_ERROR_MSG
        + "'status' will be set to enabled (you MUST reference 'status' in the 'proposed_changes' parameter!)\n"
    )


def test_check_fields_are_mentioned_to_the_client_returns_error_msg_for_two_fields() -> (
    None
):
    modification_question = "Do you approve?"
    ad = AdTest(ad_name="test", status="enabled")
    error_msg = check_fields_are_mentioned_to_the_client(ad, modification_question)
    assert error_msg == (
        FIELDS_ARE_NOT_MENTIONED_ERROR_MSG
        + "'ad_name' will be set to test (you MUST reference 'ad_name' in the 'proposed_changes' parameter!)\n"
        + "'status' will be set to enabled (you MUST reference 'status' in the 'proposed_changes' parameter!)\n"
    )


def test_check_fields_are_mentioned_to_the_client_returns_empty_string_when_everything_is_ok() -> (
    None
):
    modification_question = (
        "Do you approve changing the ad_name to test and status to enabled?"
    )
    ad = AdTest(ad_name="test", status="enabled")
    error_msg = check_fields_are_mentioned_to_the_client(ad, modification_question)
    assert error_msg == ""


def test_google_ads_create_update_raises_error() -> None:
    clients_question_answere_list: List[Tuple[str, Optional[str]]] = [
        ("modification_question", "yes")
    ]
    modification_question = "Do you approve?"
    clients_approval_message = "yes"
    ad = AdTest(ad_name="test", status="enabled")
    with pytest.raises(ValueError) as e:
        google_ads_create_update(
            user_id=-1,
            conv_id=-1,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=ad,
            clients_question_answere_list=clients_question_answere_list,
        )

    assert e.value.args[0] == (
        FIELDS_ARE_NOT_MENTIONED_ERROR_MSG
        + "'ad_name' will be set to test (you MUST reference 'ad_name' in the 'proposed_changes' parameter!)\n"
        + "'status' will be set to enabled (you MUST reference 'status' in the 'proposed_changes' parameter!)\n"
        + "\n\n"
        + NOT_IN_QUESTION_ANSWER_LIST
    )
