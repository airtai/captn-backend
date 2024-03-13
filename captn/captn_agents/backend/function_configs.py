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

change_google_account_config = {
    "name": "change_google_account",
    "description": """This method should be used only when the client explicitly asks for the change of the Google account (the account which will be used for Google Ads)!""",
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
    "description": """Query the Google Ads API.
If not told differently, do NOT retrieve information about the REMOVED resources (campaigns, ad groups, ads...) i.e. use the 'WHERE' clause to filter out the REMOVED resources!""",
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


MODIFICATION_WARNING = """VERY IMPORTANT:
DO NOT call this function without the clients explicit approval to modify the resource!!!.
i.e. the client must answer 'yes' to the question which asks for the permission to make the changes!
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
The client can approve by answering 'Yes' to the question. If the answer is 'Yes ...', the modification will NOT be approved - the answer must be 'Yes' and nothing else.
NEVER create this message on your own, or modify clients message in ANY way!
Faking the clients approval may resault with the LAWSUIT and you will get fired!!""",
    },
    "modification_question": {
        "type": "string",
        "description": """Make sure that the 'proposed_changes' parameter you have used in the 'ask_client_for_permission' function is the same as the 'modification_question' you are currently using (EVERY character must be the same).""",
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
    "path1": {
        "type": "string",
        "description": "First part of text that can be appended to the URL in the ad. To delete the current value, set this field to an empty string. This field can ONLY be set to empty when path2 is also empty!",
    },
    "path2": {
        "type": "string",
        "description": "Second part of text that can be appended to the URL in the ad. This field can ONLY be set when path1 is also set! To delete the current value, set this field to an empty string.",
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
            "modification_question": properties_config["modification_question"],
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
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
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
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
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
            "modification_question",
        ],
    },
}


create_ad_group_ad_config = {
    "name": "create_ad_group_ad",
    "description": f"""Create Google Ad.
It is not mandatory but it is recommended to use (Display) path1 and path2 parameters.
Use this method only when the client approves the creation of the new Ad, ALL the headlines, descriptions and final_url.
{MODIFICATION_WARNING}""",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "ad_group_id": properties_config["ad_group_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "modification_question": properties_config["modification_question"],
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
            "path1": properties_config["path1"],
            "path2": properties_config["path2"],
        },
        "required": [
            "customer_id",
            "ad_group_id",
            "clients_approval_message",
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
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
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
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
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
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
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
            "headline": properties_config["headline"],
            "description": properties_config["description"],
        },
        "required": [
            "customer_id",
            "ad_id",
            "clients_approval_message",
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
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
            "path1": properties_config["path1"],
            "path2": properties_config["path2"],
        },
        "required": [
            "customer_id",
            "ad_id",
            "clients_approval_message",
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
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
            "modification_question",
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

ask_client_for_permission_config = {
    "description": """Ask the client for permission to make the changes. Use this method before calling any of the modification methods!
Use 'resource_details' to describe in detail the resource which you want to modify (all the current details of the resource) and 'proposed_changes' to describe the changes which you want to make.
Do NOT use this method before you have all the information about the resource and the changes which you want to make!
This method should ONLY be used when you know the exact resource and exact changes which you want to make and NOT for the general questions like: 'Do you want to update keywords?'.
Also, propose one change at a time. If you want to make multiple changes, ask the client for the permission for each change separately i.e. before each modification, use this method to ask the client for the permission.
At the end of the message, inform the client that the modifications will be made ONLY if he answers explicitly 'Yes'.""",
    "name": "ask_client_for_permission",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Id of the customer for whom the changes will be made",
            },
            "resource_details": {
                "type": "string",
                "description": """Make sure you add all the information which the client needs to know, beacuse the client does NOT see the internal team messages!
You MUST also describe to the client the current situation for that resource.
If you want to modify the Ad Copy, you MUST provide the current Ad Copy details, e.g:
The current Ad Copy contains 3 headlines and 2 descriptions. The headlines are 'h1', 'h2' and 'h3'. The descriptions are 'd1' and 'd2'.

If you want to modify the keywords, you MUST provide the current keywords details, e.g:
Ad Group 'ag1' contains 5 keywords. The keywords are 'k1', 'k2', 'k3', 'k4' and 'k5'.""",
            },
            "proposed_changes": {
                "type": "string",
                "description": """Explains which changes you want to make and why you want to make them.
I suggest adding new headline 'new-h' because it can increase the CTR and the number of conversions.
You MUST also tell about all the fields which will be effected by the changes, e.g.:
'status' will be changed from 'ENABLED' to 'PAUSED'
Budget will be set to 2$ ('cpc_bid_micros' will be changed from '1000000' to '2000000')

e.g. for AdGroupAd:
'final_url' will be set to 'https://my-web-page.com'
Hedlines will be extended wit a list 'hedlines' ['h1', 'h2', 'h3', 'new-h']

Do you approve the changes? To approve the changes, please answer 'Yes' and nothing else.""",
            },
        },
        "required": ["customer_id", "resource_details", "proposed_changes"],
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
            "modification_question": properties_config["modification_question"],
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
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
            "keyword_match_type": properties_config["keyword_match_type"],
            "keyword_text": properties_config["keyword_text"],
        },
        "required": [
            "customer_id",
            "campaign_id",
            "criterion_id",
            "clients_approval_message",
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
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
            "modification_question",
        ],
    },
}

create_geo_targeting_for_campaign_config = {
    "name": "create_geo_targeting_for_campaign",
    "description": f"""Creates geographical targeting on the campaign level.
When the client provides the location names (country/city/region), use the 'location_names' parameter without the 'location_ids' parameter. By doing so, you will receive a list of avaliable locations and their IDs.
Once the client approves the locations, you can use the 'location_ids' parameter to create the geo targeting for the campaign.
location_ids and location_names parameters are mutually exclusive and they can NOT be set to None at the same time.
{MODIFICATION_WARNING}""",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": properties_config["customer_id"],
            "campaign_id": properties_config["campaign_id"],
            "clients_approval_message": properties_config["clients_approval_message"],
            "modification_question": properties_config["modification_question"],
            "negative": {
                "type": "boolean",
                "description": "Whether to target (False) or exclude (True) the criterion. Default is False.",
            },
            "location_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of location IDs",
            },
            "location_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of location names e.g. ['Croaita', 'Zagreb']. These values MUST be provided by the client, do NOT improvise!",
            },
        },
        "required": [
            "customer_id",
            "campaign_id",
            "clients_approval_message",
            "modification_question",
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
            "modification_question": properties_config["modification_question"],
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
            "modification_question",
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
            "proposed_user_actions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of proposed user actions",
            },
        },
        "required": ["proposed_user_actions"],
    },
}
