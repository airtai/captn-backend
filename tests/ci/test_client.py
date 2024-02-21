import pytest

from captn.google_ads.client import (
    NOT_APPROVED,
    NOT_IN_QUESTION_ANSWER_LIST,
    _check_for_client_approval,
    clean_error_response,
)


def test_clean_error_response() -> None:
    content = b'{"detail":"(<_InactiveRpcError of RPC that terminated with:\\n\\tstatus = StatusCode.INVALID_ARGUMENT\\n\\tdetails = \\"Request contains an invalid argument.\\"\\n\\tdebug_error_string = \\"UNKNOWN:Error received from peer ipv4:142.250.184.138:443 {created_time:\\"2024-01-31T10:13:18.977793+01:00\\", grpc_status:3, grpc_message:\\"Request contains an invalid argument.\\"}\\"\\n>, <_InactiveRpcError of RPC that terminated with:\\n\\tstatus = StatusCode.INVALID_ARGUMENT\\n\\tdetails = \\"Request contains an invalid argument.\\"\\n\\tdebug_error_string = \\"UNKNOWN:Error received from peer ipv4:142.250.184.138:443 {created_time:\\"2024-01-31T10:13:18.977793+01:00\\", grpc_status:3, grpc_message:\\"Request contains an invalid argument.\\"}\\"\\n>, errors {\\n  error_code {\\n    query_error: PROHIBITED_RESOURCE_TYPE_IN_SELECT_CLAUSE\\n  }\\n  message: \\"Cannot select fields from the following resources: \\\\\'AD_GROUP_CRITERION\\\\\', \\\\\'AD_GROUP\\\\\', since the resource is incompatible with the resource in FROM clause.\\"\\n}\\nrequest_id: \\"-3cDGJ1vaY4dJymqB5Ylag\\"\\n, \'-3cDGJ1vaY4dJymqB5Ylag\')"}'
    expected = "  message: \"Cannot select fields from the following resources: \\'AD_GROUP_CRITERION\\', \\'AD_GROUP\\', since the resource is incompatible with the resource in FROM clause.\""

    assert clean_error_response(content) == expected


def test_check_for_client_approval() -> None:
    response = _check_for_client_approval(
        clients_approval_message="yes ",
        modification_question="modification_question",
        clients_question_answere_list=[("modification_question", "yes ")],
    )
    assert response


def test_check_for_client_approval_not_in_qa_list() -> None:
    with pytest.raises(ValueError) as exc_info:
        _check_for_client_approval(
            clients_approval_message="yes",
            modification_question="modification_question",
            clients_question_answere_list=[("aa", "bb")],
        )
    assert exc_info.value.args[0] == NOT_IN_QUESTION_ANSWER_LIST


def test_check_for_client_approval_client_did_not_approve() -> None:
    with pytest.raises(ValueError) as exc_info:
        _check_for_client_approval(
            clients_approval_message="yes 123",
            modification_question="modification_question",
            clients_question_answere_list=[("modification_question", "yes 123")],
        )
    assert exc_info.value.args[0] == NOT_APPROVED
