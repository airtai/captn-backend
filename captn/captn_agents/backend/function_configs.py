create_execution_team_config = {
    "name": "create_execution_team",
    "description": "Create the team which will execute the plan",
    "parameters": {
        "type": "object",
        "properties": {
            "plan": {
                "type": "string",
                "description": "The plan for the execution team",
            },
            "roles": {
                "type": "string",
                "description": "List of the team roles in charge of executing the plan (e.g. roles=['QA', 'Developer', 'Systrem_Arhitect'])",
            },
        },
        "required": ["plan, roles"],
    },
}

ask_for_additional_info_config = {
    "name": "ask_for_additional_info",
    "description": "Ask your supervisor (a person outside of your team) for additional information",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Question for the supervisor",
            },
        },
        "required": ["question"],
    },
}

answer_to_execution_team_config = {
    "name": "answer_to_execution_team",
    "description": "Answer to the question which was asked by the execution team",
    "parameters": {
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": "The answer to the question",
            },
            "team_name": {
                "type": "string",
                "description": "Name of the team which asked the question",
            },
        },
        "required": ["answer", "team_name"],
    },
}

list_files_config = {
    "name": "list_files",
    "description": "List all the files in the directory",
    "parameters": {
        "type": "object",
        "properties": {
            "directory_path": {
                "type": "string",
                "description": "The path to the directory",
            },
        },
        "required": ["directory_path"],
    },
}

write_to_file_config = {
    "name": "write_to_file",
    "description": "Writes the content into a file",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "The name of the file",
            },
            "content": {
                "type": "string",
                "description": "The content which neeeds to be written into the file",
            },
        },
        "required": ["filename", "content"],
    },
}

read_file_config = {
    "name": "read_file",
    "description": "Reads the content of the file",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "The name of the file",
            },
        },
        "required": ["filename"],
    },
}


execute_command_config = {
    "name": "execute_command",
    "description": "Command which needs to be executed",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Command which needs to be executed e.g. '['pytest']'",
            },
        },
        "required": ["command"],
    },
}


create_team_config = {
    "name": "create_team",
    "description": "Create an ad-hoc team to solve the problem",
    "parameters": {
        "type": "object",
        "properties": {
            "json_as_a_string": {
                "type": "string",
                "description": "a JSON-encoded string with all parameters",
            },
        },
        "required": ["json_as_a_string"],
    },
}

answer_to_team_lead_question_config = {
    "name": "answer_to_team_lead_question",
    "description": "Answer to the team leaders question",
    "parameters": {
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": "The answer to the team leaders question",
            },
            "team_name": {
                "type": "string",
                "description": "Name of the team which asked the question",
            },
        },
        "required": ["answer", "team_name"],
    },
}

get_login_url_config = {
    "name": "get_login_url",
    "description": "Get the users login url",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

list_accessible_customers_config = {
    "name": "list_accessible_customers",
    "description": "List all the customers accessible to the user",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

execute_query_config = {
    "name": "execute_query",
    "description": "Query the Google Ads API",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_ids": {
                "type": "string",
                # "type": "array",
                # "items": {"type": "string"},
                "description": "List of customer ids",
            },
            "query": {
                "type": "string",
                "description": "Database query",
            },
        },
    },
}

create_google_ads_team_config = {
    "name": "create_google_ads_team",
    "description": "Create Google Ads team for solving the task",
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "A task which needs to be solved",
            },
        },
        "required": ["task"],
    },
}

answer_the_question_config = {
    "name": "answer_the_question",
    "description": "Answer to the question",
    "parameters": {
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": "The answer to the question",
            },
            "team_name": {
                "type": "string",
                "description": "Name of the team which asked the question",
            },
        },
        "required": ["answer", "team_name"],
    },
}

calculate_credit_config = {
    "name": "calculate_credit",
    "description": "Calculate the credit",
    "parameters": {
        "type": "object",
        "properties": {
            "credit_duration": {
                "type": "string",
                "description": "Loan repayment term",
            },
            "amount_euro": {
                "type": "string",
                "description": "Total loan amount in euros",
            },
        },
        "required": ["credit_duration", "amount_euro"],
    },
}

create_banking_credit_calculation_team_config = {
    "name": "create_banking_credit_calculation_team",
    "description": "Create banking team dedicated for the credit calculation",
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "A task which needs to be solved",
            },
        },
        "required": ["task"],
    },
}

reply_to_client_config = {
    "name": "reply_to_client",
    "description": "Respond to the client (answer to his task or question for additional information)",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Message for the client",
            },
        },
        "required": ["message"],
    },
}

analyze_query_response_config = {
    "name": "analyze_query_response",
    "description": "Analyze the execute_query response",
    "parameters": {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "The name of the file where the response is saved",
            },
        },
        "required": ["file_name"],
    },
}

update_ad_group_config = {
    "name": "update_ad_group",
    "description": "Update Google Ad Group",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Id of the customer",
            },
            "ad_group_id": {
                "type": "string",
                "description": "Id of the Ad group",
            },
            "ad_id": {
                "type": "string",
                "description": "Id of the Ad",
            },
            "clients_approval_message": {
                "type": "string",
                "description": "Client approval message",
            },
            "client_approved_modicifation_for_this_resource": {
                "type": "boolean",
                "description": """The team must inform the client about all changes which will be made
and which values will be modified (e.g. name, status...).
Client must be informed about everything!""",
            },
            "name": {
                "type": "string",
                "description": "The name of the Ad",
            },
            "cpc_bid_micros": {
                "type": "integer",
                "description": "Cost per click bid micros",
            },
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
        },
        "required": [
            "customer_id",
            "ad_group_id",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}


update_ad_config = {
    "name": "update_ad",
    "description": "Update Google Ad",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Id of the customer",
            },
            "ad_group_id": {
                "type": "string",
                "description": "Id of the Ad group",
            },
            "ad_id": {
                "type": "string",
                "description": "Id of the Ad",
            },
            "clients_approval_message": {
                "type": "string",
                "description": "Client approval message",
            },
            "client_approved_modicifation_for_this_resource": {
                "type": "boolean",
                "description": """The team must inform the client about all changes which will be made
and which values will be modified (e.g. name, status...).
Client must be informed about everything!""",
            },
            "cpc_bid_micros": {
                "type": "integer",
                "description": "Cost per click bid micros",
            },
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
        },
        "required": [
            "customer_id",
            "ad_group_id",
            "ad_id",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}


update_campaign_config = {
    "name": "update_campaign",
    "description": "Update Google Ads Campaign",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Id of the customer",
            },
            "campaign_id": {
                "type": "string",
                "description": "Id of the campaign",
            },
            "clients_approval_message": {
                "type": "string",
                "description": "Client approval message",
            },
            "client_approved_modicifation_for_this_resource": {
                "type": "boolean",
                "description": """The team must inform the client about all changes which will be made
and which values will be modified (e.g. name, status...).
Client must be informed about everything!""",
            },
            "name": {
                "type": "string",
                "description": "The name of the Ad",
            },
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
        },
        "required": [
            "customer_id",
            "campaign_id",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}

update_ad_group_criterion_config = {
    "name": "update_ad_group_criterion",
    "description": "Update Google Ads Group Criterion",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Id of the customer",
            },
            "ad_group_id": {
                "type": "string",
                "description": "Id of the Ad group",
            },
            "criterion_id": {
                "type": "string",
                "description": "Id of the Ad group criterion",
            },
            "clients_approval_message": {
                "type": "string",
                "description": "Client approval message",
            },
            "client_approved_modicifation_for_this_resource": {
                "type": "boolean",
                "description": """The team must inform the client about all changes which will be made
and which values will be modified (e.g. name, status...).
Client must be informed about everything!""",
            },
            "name": {
                "type": "string",
                "description": "The name of the Ad",
            },
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
            "cpc_bid_micros": {
                "type": "integer",
                "description": "Cost per click bid micros",
            },
        },
        "required": [
            "customer_id",
            "ad_group_id",
            "criterion_id",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}

update_ad_copy_config = {
    "name": "update_ad_copy",
    "description": "Update Google Ads Ad Copy",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Id of the customer",
            },
            "ad_id": {
                "type": "string",
                "description": "Id of the Ad",
            },
            "clients_approval_message": {
                "type": "string",
                "description": "Client approval message",
            },
            "client_approved_modicifation_for_this_resource": {
                "type": "boolean",
                "description": """The team must inform the client about all changes which will be made
and which values will be modified (e.g. name, status...).
Client must be informed about everything!""",
            },
            "headline": {
                "type": "string",
                "description": "Ad Copy Headline, max_length=30",
            },
            "description": {
                "type": "string",
                "description": "Ad Copy Description, max_length=90",
            },
            "update_existing_headline_index": {
                "type": "string",
                "description": """Index in the headlines list which needs to be updated. Index starts from 0.
Use this parameter ONLY when you want to modify existing headline!""",
            },
            "update_existing_description_index": {
                "type": "string",
                "description": """Index in the descriptions list which needs to be updated. Index starts from 0.
Use this parameter ONLY when you want to modify existing description!""",
            },
            "final_urls": {
                "type": "string",
                "description": "Ad Copy final_urls",
            },
            "final_mobile_urls": {
                "type": "string",
                "description": "Ad Copy final_mobile_urls",
            },
        },
        "required": [
            "customer_id",
            "ad_id",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}


reply_to_client_2_config = {
    "name": "reply_to_client",
    "description": "Respond to the client (answer to his task or question for additional information)",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Message for the client",
            },
            "smart_suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "description": """List of quick replies which the client can use for incoming message. e.g. ['Yes', 'No'].
If you do not want to use smart suggestions, set this parameter to an empty list: []""",
            },
            "is_question": {
                "type": "boolean",
                "description": "Is the message a question for additional info from the client",
            },
            "completed": {
                "type": "boolean",
                "description": "Has the team completed the task or are they waiting for additional info",
            },
        },
        "required": ["message", "is_question", "completed", "smart_suggestions"],
    },
}

create_negative_keyword_for_campaign_config = {
    "name": "create_negative_keyword_for_campaign",
    "description": "Creates Negative campaign keywords (CampaignCriterion)",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Id of the customer",
            },
            "campaign_id": {
                "type": "string",
                "description": "Id of the campaign",
            },
            "clients_approval_message": {
                "type": "string",
                "description": "Client approval message",
            },
            "client_approved_modicifation_for_this_resource": {
                "type": "boolean",
                "description": """The team must inform the client about all changes which will be made
and which values will be modified (e.g. name, status...).
Client must be informed about everything!""",
            },
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
            "keyword_match_type": {
                "type": "string",
                "description": "The match type of the keyword.",
            },
            "keyword_text": {
                "type": "string",
                "description": "The text of the keyword",
            },
            "negative": {
                "type": "boolean",
                "description": "Whether to target (false) or exclude (true) the criterion",
            },
            "bid_modifier": {
                "type": "number",
                "description": "The modifier for the bids when the criterion matches.",
            },
        },
        "required": [
            "customer_id",
            "campaign_id",
            "keyword_match_type",
            "keyword_text",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}

create_keyword_for_ad_group_config = {
    "name": "create_keyword_for_ad_group",
    "description": "Creates (regular and negative) keywords for Ad Group (AdGroupCriterion)",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Id of the customer",
            },
            "ad_group_id": {
                "type": "string",
                "description": "Id of the Ad group",
            },
            "clients_approval_message": {
                "type": "string",
                "description": "Client approval message",
            },
            "client_approved_modicifation_for_this_resource": {
                "type": "boolean",
                "description": """The team must inform the client about all changes which will be made
and which values will be modified (e.g. name, status...).
Client must be informed about everything!""",
            },
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
            "keyword_match_type": {
                "type": "string",
                "description": "The match type of the keyword.",
            },
            "keyword_text": {
                "type": "string",
                "description": "The text of the keyword",
            },
            "negative": {
                "type": "boolean",
                "description": "Whether to target (false) or exclude (true) the criterion",
            },
            "bid_modifier": {
                "type": "number",
                "description": "The modifier for the bids when the criterion matches.",
            },
        },
        "required": [
            "customer_id",
            "ad_group_id",
            "keyword_match_type",
            "keyword_text",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}

remove_google_ads_resource_config = {
    "name": "remove_google_ads_resource",
    "description": "Removes the google ads resource",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Id of the customer",
            },
            "resource_id": {
                "type": "string",
                "description": "Id of the resource which will be removed",
            },
            "resource_type": {
                "type": "string",
                "description": """One of the following:
Literal['campaign', 'ad_group', 'ad', 'ad_group_criterion', 'campaign_criterion']""",
            },
            "clients_approval_message": {
                "type": "string",
                "description": "Client approval message",
            },
            "client_approved_modicifation_for_this_resource": {
                "type": "boolean",
                "description": """The team must inform the client about all changes which will be made
and which values will be modified (e.g. name, status...).
Client must be informed about everything!""",
            },
            "parent_id": {
                "type": "string",
                "description": """Id of the parent resorce, campaign and ad group do not have parent,
ad and ad_group_criterion uses uses ad_group_id, campaign_criterion uses campaign_id""",
            },
        },
        "required": [
            "customer_id",
            "resource_id",
            "resource_type",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}
