import unittest

import pytest
from requests.models import Response

from captn.google_ads.client import (
    ALREADY_AUTHENTICATED,
    AUTHENTICATION_ERROR,
    NOT_APPROVED,
    NOT_IN_QUESTION_ANSWER_LIST,
    check_for_client_approval,
    clean_error_response,
    clean_nones,
    execute_query,
)


def test_clean_error_response() -> None:
    content = b'{"detail":"(<_InactiveRpcError of RPC that terminated with:\\n\\tstatus = StatusCode.INVALID_ARGUMENT\\n\\tdetails = \\"Request contains an invalid argument.\\"\\n\\tdebug_error_string = \\"UNKNOWN:Error received from peer ipv4:142.250.184.138:443 {created_time:\\"2024-01-31T10:13:18.977793+01:00\\", grpc_status:3, grpc_message:\\"Request contains an invalid argument.\\"}\\"\\n>, <_InactiveRpcError of RPC that terminated with:\\n\\tstatus = StatusCode.INVALID_ARGUMENT\\n\\tdetails = \\"Request contains an invalid argument.\\"\\n\\tdebug_error_string = \\"UNKNOWN:Error received from peer ipv4:142.250.184.138:443 {created_time:\\"2024-01-31T10:13:18.977793+01:00\\", grpc_status:3, grpc_message:\\"Request contains an invalid argument.\\"}\\"\\n>, errors {\\n  error_code {\\n    query_error: PROHIBITED_RESOURCE_TYPE_IN_SELECT_CLAUSE\\n  }\\n  message: \\"Cannot select fields from the following resources: \\\\\'AD_GROUP_CRITERION\\\\\', \\\\\'AD_GROUP\\\\\', since the resource is incompatible with the resource in FROM clause.\\"\\n}\\nrequest_id: \\"-3cDGJ1vaY4dJymqB5Ylag\\"\\n, \'-3cDGJ1vaY4dJymqB5Ylag\')"}'
    expected = "  message: \"Cannot select fields from the following resources: \\'AD_GROUP_CRITERION\\', \\'AD_GROUP\\', since the resource is incompatible with the resource in FROM clause.\""

    assert clean_error_response(content) == expected


def test_remove_none_values() -> None:
    original = {"ad_id": None, "ad_name": "test", "status": None}
    expected = {"ad_name": "test"}
    assert clean_nones(original) == expected


def test_remove_none_values_nested() -> None:
    original = {
        "ad_group": {
            "name": "Sofas",
            "ad_group_id": None,
        },
        "customer_id": None,
        "keywords": [
            {
                "ad_group_id": None,
                "keyword_match_type": "BROAD",
            },
        ],
    }

    expected = {
        "ad_group": {
            "name": "Sofas",
        },
        "keywords": [
            {
                "keyword_match_type": "BROAD",
            },
        ],
    }

    assert clean_nones(original) == expected


def test_check_for_client_approval_not_in_qa_list() -> None:
    input_parameters = {"ad_name": "test"}
    clients_question_answer_list = [
        ({"ad_name": "test2"}, "No"),
        ({"ad_name": "test3"}, "Yes"),
    ]
    error_msg = check_for_client_approval(
        modification_function_parameters=input_parameters,
        clients_question_answer_list=clients_question_answer_list,
    )
    assert NOT_IN_QUESTION_ANSWER_LIST in error_msg


def test_check_for_client_approval_client_did_not_approve() -> None:
    input_parameters = {"ad_name": "test"}
    clients_question_answer_list = [
        ({"ad_name": "test"}, "No"),
        ({"ad_name": "test3"}, "No"),
    ]
    error_msg = check_for_client_approval(
        modification_function_parameters=input_parameters,
        clients_question_answer_list=clients_question_answer_list,
    )
    assert error_msg.strip() == NOT_APPROVED


def test_check_for_client_approval_client_approved_second_time() -> None:
    input_parameters = {"ad_name": "test"}
    clients_question_answer_list = [
        ({"ad_name": "test8"}, "No"),
        ({"ad_name": "test"}, "No"),
        ({"ad_name": "test"}, "Yes"),
    ]
    error_msg = check_for_client_approval(
        modification_function_parameters=input_parameters,
        clients_question_answer_list=clients_question_answer_list,
    )
    assert error_msg is None


@pytest.mark.parametrize(
    "error_message", ["account_not_enabled", "authentication_error"]
)
def test_execute_query_when_google_ads_api_raises_error(error_message) -> None:
    error_dict = {
        "account_not_enabled": {
            "content": b'{"detail":"(<_InactiveRpcError of RPC that terminated with:\\n\\tstatus = StatusCode.PERMISSION_DENIED\\n\\tdetails = \\"The caller does not have permission\\"\\n\\tdebug_error_string = \\"UNKNOWN:Error received from peer {created_time:\\"2024-05-14T10:33:11\\", grpc_status:7, grpc_message:\\"The caller does not have permission\\"}\\"\\n>, <_InactiveRpcError of RPC that terminated with:\\n\\tstatus = StatusCode.PERMISSION_DENIED\\n\\tdetails = \\"The caller does not have permission\\"\\n\\tdebug_error_string = \\"UNKNOWN:Error received from peer ipv4:142.250.184.138:443 {created_time:\\"2024-05-14T10:33:11\\", grpc_status:7, grpc_message:\\"The caller does not have permission\\"}\\"\\n>, errors {\\n  error_code {\\n    authorization_error: CUSTOMER_NOT_ENABLED\\n  }\\n  message: \\"The customer account can\\\\\'t be accessed because it is not yet enabled or has been deactivated.\\"})"}',
            "excepted_substr": "If you have just created the account, please wait for a few hours before trying again.",
        },
        "authentication_error": {
            "content": b'{"detail":"Please try to execute the command again."}',
            "excepted_substr": AUTHENTICATION_ERROR,
        },
    }

    with (
        unittest.mock.patch(
            "captn.google_ads.client.get_login_url",
            return_value={"login_url": ALREADY_AUTHENTICATED},
        ),
        unittest.mock.patch(
            "captn.google_ads.client.requests_get",
        ) as mock_requests_get,
    ):
        response = Response()
        response.status_code = 500
        response._content = error_dict[error_message]["content"]
        mock_requests_get.return_value = response

        with pytest.raises(ValueError) as exc_info:
            execute_query(user_id=-1, conv_id=-1)

        assert (
            error_dict[error_message]["excepted_substr"] in exc_info.value.args[0]
        ), exc_info.value.args[0]
