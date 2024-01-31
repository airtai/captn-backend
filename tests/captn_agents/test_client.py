from captn.google_ads.client import clean_error_response


def test_clean_error_response() -> None:
    content = b'{"detail":"(<_InactiveRpcError of RPC that terminated with:\\n\\tstatus = StatusCode.INVALID_ARGUMENT\\n\\tdetails = \\"Request contains an invalid argument.\\"\\n\\tdebug_error_string = \\"UNKNOWN:Error received from peer ipv4:142.250.184.138:443 {created_time:\\"2024-01-31T10:13:18.977793+01:00\\", grpc_status:3, grpc_message:\\"Request contains an invalid argument.\\"}\\"\\n>, <_InactiveRpcError of RPC that terminated with:\\n\\tstatus = StatusCode.INVALID_ARGUMENT\\n\\tdetails = \\"Request contains an invalid argument.\\"\\n\\tdebug_error_string = \\"UNKNOWN:Error received from peer ipv4:142.250.184.138:443 {created_time:\\"2024-01-31T10:13:18.977793+01:00\\", grpc_status:3, grpc_message:\\"Request contains an invalid argument.\\"}\\"\\n>, errors {\\n  error_code {\\n    query_error: PROHIBITED_RESOURCE_TYPE_IN_SELECT_CLAUSE\\n  }\\n  message: \\"Cannot select fields from the following resources: \\\\\'AD_GROUP_CRITERION\\\\\', \\\\\'AD_GROUP\\\\\', since the resource is incompatible with the resource in FROM clause.\\"\\n}\\nrequest_id: \\"-3cDGJ1vaY4dJymqB5Ylag\\"\\n, \'-3cDGJ1vaY4dJymqB5Ylag\')"}'
    expected = "  message: \"Cannot select fields from the following resources: \\'AD_GROUP_CRITERION\\', \\'AD_GROUP\\', since the resource is incompatible with the resource in FROM clause.\""

    assert clean_error_response(content) == expected
