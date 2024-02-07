from ..model import suggestions_description, type_description
from .functions import (
    reply_to_client_2_description,
    smart_suggestions_description,
)

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
                "type": "array",
                "items": {"type": "string"},
                "description": "List of customer ids",
            },
            "query": {
                "type": "string",
                "description": """Database query.
Unless told differently, do NOT retrieve information about the REMOVED resources (campaigns, ad groups, ads...)!
NEVER try to retrieve field "ad_group_ad.ad.strength" because field "strength" does NOT exist!""",
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


MODIFICATION_WARNING = """VERY IMPORTANT:
DO NOT call this function without the clients explicit approval to modify the resource!!!.
The client must also approve ALL the parameters which will be used for the modification. Otherwise you will be penalized!
If a client only asks for some suggestions, then clients_approval_message parameter MUST be set to None and
client_approved_modicifation_for_this_resource parameter MUST be set to False! Otherwise you will be penalized!
"""

properties_config = {
    "customer_id": {
        "type": "string",
        "description": "Id of the customer",
    },
    "campaign_id": {
        "type": "string",
        "description": "Id of the campaign",
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
        "description": """Clients approval message.
Clients meassage in which he approves the changes.
NEVER create this message on your own, or modify clients message in ANY way!
Faking the clients approval may resault with the LAWSUIT and you will get fired!!""",
    },
    "client_approved_modicifation_for_this_resource": {
        "type": "boolean",
        "description": """The team must inform the client about all changes which will be made
and which values will be modified (e.g. name, status...). ONLY if the client APPROVES the changes, the team can use this function.
Until the client approves the changes, the team must NOT call the function! and this parameter MUST be set to False.
Client must be informed about everything!""",
    },
    "cpc_bid_micros": {
        "type": "integer",
        "description": "Cost per click bid micros",
    },
    "headline": {
        "type": "string",
        "description": "Ad Copy Headline, MAXIMUM 30 characters!",
    },
    "description": {
        "type": "string",
        "description": "Ad Copy Description, MAXIMUM 90 characters!",
    },
    "keyword_match_type": {
        "type": "string",
        "description": "The match type of the keyword.",
    },
    "keyword_text": {
        "type": "string",
        "description": "The text of the keyword",
    },
    "final_url": {
        "type": "string",
        "description": "The page on the website that people reach when they click the ad. final_url must use HTTP or HTTPS protocol. The url should only contain the website domain WITHOUT the path. e.g. https://www.example.com",
    },
}


update_ad_group_config = {
    "name": "update_ad_group",
    "description": f"Update Google Ad Group. {MODIFICATION_WARNING}",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "ad_group_id": properties_config["ad_group_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "name": {
                "type": "string",
                "description": "The name of the Ad Group",
            },
            "cpc_bid_micros": properties_config["cpc_bid_micros"],
            "status": {
                "type": "string",
                "description": "The status of the Ad Group (ENABLED or PAUSED)",
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

create_ad_group_config = {
    "name": "create_ad_group",
    "description": f"Create Google Ad Group. {MODIFICATION_WARNING}",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "campaign_id": properties_config["campaign_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "name": {
                "type": "string",
                "description": "The name of the Ad Group",
            },
            "cpc_bid_micros": properties_config["cpc_bid_micros"],
            "status": {
                "type": "string",
                "description": "The status of the Ad Group (ENABLED or PAUSED)",
            },
        },
        "required": [
            "customer_id",
            "campaign_id",
            "name",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}


update_ad_group_ad_config = {
    "name": "update_ad_group_ad",
    "description": f"Update Google Ad. {MODIFICATION_WARNING}",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "ad_group_id": properties_config["ad_group_id"],
            "ad_id": properties_config["ad_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "cpc_bid_micros": properties_config["cpc_bid_micros"],
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


create_ad_group_ad_config = {
    "name": "create_ad_group_ad",
    "description": f"""Create Google Ad.
Use this method only when the client approves the creation of the new Ad, ALL the headlines, descriptions and final_url.
{MODIFICATION_WARNING}""",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "ad_group_id": properties_config["ad_group_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
            "headlines": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of headlines, MINIMUM 3, MAXIMUM 15 headlines. Each headline MUST be LESS than 30 characters!",
            },
            "descriptions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of descriptions, MINIMUM 2, MAXIMUM 4 descriptions. Each description MUST be LESS than 90 characters!",
            },
            "final_url": properties_config["final_url"],
        },
        "required": [
            "customer_id",
            "ad_group_id",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
            "headlines",
            "descriptions",
            "final_url",
        ],
    },
}

update_campaign_config = {
    "name": "update_campaign",
    "description": f"Update Google Ads Campaign. {MODIFICATION_WARNING}",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "campaign_id": properties_config["campaign_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
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

create_campaign_config = {
    "name": "create_campaign",
    "description": f"Creates Google Ads Campaign. {MODIFICATION_WARNING}",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "name": {
                "type": "string",
                "description": "The name of the Ad",
            },
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
            "budget_amount_micros": {
                "type": "number",
                "description": """The amount of the budget, in the LOCAL CURRENCY for the account (defined in the local_currency parameter).
Amount is specified in micros, where one million is equivalent to one currency unit. Monthly spend is capped at 30.4 times this amount.
Make sure that the client APPROVES the budget amount, otherwise you will be penalized!
This is the MOST IMPORTANT parameter, because it determines how much money will be spent on the ads!""",
            },
            "local_currency": {
                "type": "string",
                "description": """The currency which will be used for the budget amount.
This value MUST be found in the 'customer' table! query example: SELECT customer.currency_code FROM customer WHERE customer.id = '1212121212'""",
            },
            "network_settings_target_google_search": {
                "type": "boolean",
                "description": "Whether ads will be served with google.com search results.",
            },
            "network_settings_target_search_network": {
                "type": "boolean",
                "description": "Whether ads will be served on partner sites in the Google Search Network (requires network_settings_target_google_search to also be true).",
            },
            "network_settings_target_content_network": {
                "type": "boolean",
                "description": "Whether ads will be served on specified placements in the Google Display Network. Placements are specified using the Placement criterion.",
            },
            # "network_settings_target_partner_search_network": {
            #     "type": "boolean",
            #     "description": "Whether ads will be served on the Google Partner Network. This is available only to some select Google partner accounts.",
            # },
        },
        "required": [
            "customer_id",
            "name",
            "budget_amount_micros",
            "local_currency",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}

update_ad_group_criterion_config = {
    "name": "update_ad_group_criterion",
    "description": f"Update Google Ads Group Criterion. {MODIFICATION_WARNING}",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "ad_group_id": properties_config["ad_group_id"],
            "criterion_id": {
                "type": "string",
                "description": "Id of the Ad group criterion",
            },
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
            "cpc_bid_micros": properties_config["cpc_bid_micros"],
            "keyword_match_type": properties_config["keyword_match_type"],
            "keyword_text": properties_config["keyword_text"],
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

create_ad_copy_headline_or_description_config = {
    "name": "create_ad_copy_headline_or_description",
    "description": f"""Create NEW headline and/or description in the the Google Ads Copy.
This method does NOT create new Ad Copy, it only creates new headlines and/or descriptions for the existing Ad Copy.
This method should NOT be used for updating existing headlines or descriptions.
{MODIFICATION_WARNING}""",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "ad_id": properties_config["ad_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "headline": properties_config["headline"],
            "description": properties_config["description"],
        },
        "required": [
            "customer_id",
            "ad_id",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}

update_ad_copy_config = {
    "name": "update_ad_copy",
    "description": f"""Updates existing Google Ads Ad Copy.
Use 'update_existing_headline_index' if you want to modify existing headline and/or 'update_existing_description_index' to modify existing description.
{MODIFICATION_WARNING}""",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "ad_id": properties_config["ad_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "headline": properties_config["headline"],
            "description": properties_config["description"],
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
            "final_url": properties_config["final_url"],
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

remove_ad_copy_headline_or_description_config = {
    "name": "remove_ad_copy_headline_or_description",
    "description": f"""Removes existing Google Ads Ad Copy headline or/and description.
Use 'update_existing_headline_index' if you want to remove existing headline and/or 'update_existing_description_index' to remove existing description.
{MODIFICATION_WARNING}""",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "ad_id": properties_config["ad_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "update_existing_headline_index": {
                "type": "string",
                "description": """Index in the headlines list which needs to be removed. Index starts from 0.""",
            },
            "update_existing_description_index": {
                "type": "string",
                "description": """Index in the descriptions list which needs to be removed. Index starts from 0.""",
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

smart_suggestions_schema = {
    "$ref": "#/definitions/SmartSuggestions",
    "definitions": {
        "SmartSuggestions": {
            "title": "SmartSuggestions",
            "type": "object",
            "properties": {
                "suggestions": {
                    "title": "Suggestions",
                    "description": suggestions_description,
                    "type": "array",
                    "items": {"type": "string"},
                },
                "type": {
                    "title": "Type",
                    "description": type_description,
                    "enum": ["oneOf", "manyOf"],
                    "type": "string",
                },
            },
            "required": ["suggestions", "type"],
        }
    },
    "description": smart_suggestions_description,
}

reply_to_client_2_config = {
    "description": reply_to_client_2_description,
    "name": "reply_to_client",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": """Message for the client.
Make sure you add all the information which the client needs to know, beacuse the client does NOT see the internal team messages!""",
            },
            "completed": {
                "type": "boolean",
                "description": "Has the team completed the task or are they waiting for additional info",
            },
            "smart_suggestions": smart_suggestions_schema,
        },
        "required": ["message", "completed"],
    },
}

create_negative_keyword_for_campaign_config = {
    "name": "create_negative_keyword_for_campaign",
    "description": f"Creates Negative campaign keywords (CampaignCriterion). {MODIFICATION_WARNING}",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "campaign_id": properties_config["campaign_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
            "keyword_match_type": properties_config["keyword_match_type"],
            "keyword_text": properties_config["keyword_text"],
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

update_campaigns_negative_keywords_config = {
    "name": "update_campaigns_negative_keywords",
    "description": f"Update the Google Ads keywords (on campaign level). {MODIFICATION_WARNING}",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "campaign_id": properties_config["campaign_id"],
            "criterion_id": {
                "type": "string",
                "description": "Id of the Campaign criterion",
            },
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "keyword_match_type": properties_config["keyword_match_type"],
            "keyword_text": properties_config["keyword_text"],
        },
        "required": [
            "customer_id",
            "campaign_id",
            "criterion_id",
            "clients_approval_message",
            "client_approved_modicifation_for_this_resource",
        ],
    },
}

create_keyword_for_ad_group_config = {
    "name": "create_keyword_for_ad_group",
    "description": f"Creates (regular and negative) keywords for Ad Group (AdGroupCriterion). {MODIFICATION_WARNING}",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "ad_group_id": properties_config["ad_group_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
            "status": {
                "type": "string",
                "description": "The status of the Ad (ENABLED or PAUSED)",
            },
            "keyword_match_type": properties_config["keyword_match_type"],
            "keyword_text": properties_config["keyword_text"],
            "negative": {
                "type": "boolean",
                "description": "Whether to target (false) or exclude (true) the criterion",
            },
            "bid_modifier": {
                "type": "number",
                "description": "The modifier for the bids when the criterion matches.",
            },
            "cpc_bid_micros": properties_config["cpc_bid_micros"],
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
    "description": f"Removes the google ads resource. {MODIFICATION_WARNING}",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "resource_id": {
                "type": "string",
                "description": "Id of the resource which will be removed",
            },
            "resource_type": {
                "type": "string",
                "description": """One of the following:
Literal['campaign', 'ad_group', 'ad', 'ad_group_criterion', 'campaign_criterion']""",
            },
            "clients_approval_message": properties_config["clients_approval_message"],
            "client_approved_modicifation_for_this_resource": properties_config[
                "client_approved_modicifation_for_this_resource"
            ],
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


get_info_from_the_web_page_config = {
    "name": "get_info_from_the_web_page",
    "description": """Retrieve wanted information from the web page.
There is no need to test this function (by sending url: https://www.example.com).
NEVER use this function for scraping Google Ads pages (e.g. https://ads.google.com/aw/campaigns?campaignId=1212121212)
""",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The url of the web page which needs to be summarized",
            },
            "task": {
                "type": "string",
                "description": """Task which needs to be solved.
This parameter should NOT mention that we are working on some Google Ads task.
The focus of the task is usually retrieving the information from the web page e.g.: categories, products, services etc

Example 1:
task='Get all info about the clients business from the provided url.'
Example 2:
task='Get me the all the links that are present in the main navigation in the url. You need to return the output with the absolute urls.' """,
            },
            "task_guidelines": {
                "type": "string",
                "description": """Guidelines which will help you to solve the task. What information are we looking for, what questions need to be answered, etc.
This parameter should NOT mention that we are working on some Google Ads task.

Example 1:
task_guidelines='Get me all the main navigation links on the home page. I need only internal links.' """,
            },
        },
        "required": ["url", "task", "task_guidelines"],
    },
}


send_email_config = {
    "name": "send_email",
    "description": "Send email to the client.",
    "parameters": {
        "type": "object",
        "properties": {
            "daily_analysis": {
                "type": "string",
                "description": "Daily analysis of the campaign performance paragraph",
            },
            "proposed_user_actions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of proposed user actions",
            },
        },
        "required": ["daily_analysis", "proposed_user_actions"],
    },
}
