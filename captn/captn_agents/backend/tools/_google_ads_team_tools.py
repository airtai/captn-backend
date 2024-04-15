import ast
import inspect
from functools import wraps
from typing import Annotated, Any, Callable, Dict, List, Literal, Optional, Tuple, Union

from google_ads.model import (
    AdCopy,
    AdGroup,
    AdGroupAd,
    AdGroupCriterion,
    Campaign,
    CampaignCriterion,
    GeoTargetCriterion,
    RemoveResource,
)

from ....google_ads.client import execute_query as execute_query_client
from ....google_ads.client import get_login_url, google_ads_create_update
from ....google_ads.client import (
    list_accessible_customers as list_accessible_customers_client,
)
from ..toolboxes import Toolbox
from ._functions import (
    Context,
    ask_client_for_permission,
    ask_client_for_permission_description,
    get_info_from_the_web_page,
    get_info_from_the_web_page_description,
    reply_to_client_2,
    reply_to_client_2_description,
)

__all__ = (
    "add_shared_functions",
    "change_google_account",
    "change_google_account_description",
    "execute_query",
    "execute_query_description",
    "list_accessible_customers",
    "list_accessible_customers_description",
    "properties_config",
)

change_google_account_description = "This method should be used only when the client explicitly asks for the change of the Google account (the account which will be used for Google Ads)!"


def change_google_account(context: Context) -> Dict[str, str]:
    user_id = context.user_id
    conv_id = context.conv_id

    return get_login_url(user_id=user_id, conv_id=conv_id, force_new_login=True)


list_accessible_customers_description = "List all the customers accessible to the user"


def list_accessible_customers(context: Context) -> Union[List[str], Dict[str, str]]:
    user_id = context.user_id
    conv_id = context.conv_id
    get_only_non_manager_accounts = context.get_only_non_manager_accounts

    return list_accessible_customers_client(
        user_id=user_id,
        conv_id=conv_id,
        get_only_non_manager_accounts=get_only_non_manager_accounts,
    )


execute_query_description = """Query the Google Ads API.
If not told differently, do NOT retrieve information about the REMOVED resources (campaigns, ad groups, ads...) i.e. use the 'WHERE' clause to filter out the REMOVED resources!"""

query_description = """Database query.
Unless told differently, do NOT retrieve information about the REMOVED resources (campaigns, ad groups, ads...)!
NEVER try to retrieve field "ad_group_ad.ad.strength" because field "strength" does NOT exist!"""


def execute_query(
    context: Context,
    customer_ids: Annotated[Optional[List[str]], "List of customer ids"] = None,
    query: Annotated[Optional[str], query_description] = None,
) -> Union[str, Dict[str, str]]:
    user_id = context.user_id
    conv_id = context.conv_id
    return execute_query_client(
        user_id=user_id, conv_id=conv_id, customer_ids=customer_ids, query=query
    )


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
    "local_currency": {
        "type": "string",
        "description": """The currency which will be used for the budget amount.
This value MUST be found in the 'customer' table! query example: SELECT customer.currency_code FROM customer WHERE customer.id = '1212121212'
If the budget micros value is used, the currency code IS required!""",
    },
}

MODIFICATION_WARNING = """VERY IMPORTANT:
DO NOT call this function without the clients explicit approval to modify the resource!!!.
i.e. the client must answer 'yes' to the question which asks for the permission to make the changes!
"""

budget_amount_micros_description = """The DAILY amount of the budget, in the LOCAL CURRENCY for the account (defined in the local_currency parameter).
Amount is specified in micros, where one million is equivalent to one currency unit. Monthly spend is capped at 30.4 times this amount.
Make sure that the client APPROVES the budget amount, otherwise you will be penalized!
This is the MOST IMPORTANT parameter, because it determines how much money will be spent PER DAY on the ads!"""

create_campaign_description = f"Creates Google Ads Campaign. {MODIFICATION_WARNING}"


def _get_customer_currency(user_id: int, conv_id: int, customer_id: str) -> str:
    query = "SELECT customer.currency_code FROM customer"
    query_result = execute_query_client(
        user_id=user_id, conv_id=conv_id, customer_ids=[customer_id], query=query
    )

    currency = ast.literal_eval(query_result)[customer_id][0]["customer"][  # type: ignore[arg-type]
        "currencyCode"
    ]
    return currency  # type: ignore


def _check_currency(
    user_id: int, conv_id: int, customer_id: str, local_currency: Optional[str]
) -> None:
    cutomers_currency = _get_customer_currency(
        user_id=user_id, conv_id=conv_id, customer_id=customer_id
    )
    if (
        local_currency is None
        or cutomers_currency.upper() != local_currency.strip().upper()
    ):
        raise ValueError(
            f"""Error: Customer ({customer_id}) account has set currency ({cutomers_currency}) which is different from the provided currency ({local_currency=}).
Please convert the budget to the customer's currency and ask the client for the approval with the new budget amount (in the customer's currency)."""
        )


def add_currency_check(
    *,
    micros_var_name: str = "cpc_bid_micros",
) -> Callable[..., Any]:
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(f)
        params = list(sig.parameters.values())
        params.append(
            inspect.Parameter(
                "local_currency",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Annotated[
                    Optional[str], properties_config["local_currency"]["description"]
                ],
                default=None,
            )
        )
        new_sig = sig.replace(parameters=params)

        @wraps(f)
        def wrapper(
            *args: Any,
            local_currency: Annotated[
                Optional[str], properties_config["local_currency"]["description"]
            ] = None,
            **kwargs: Any,
        ) -> Any:
            customer_id: str = kwargs["customer_id"]
            context: Context = kwargs["context"]

            user_id = context.user_id
            conv_id = context.conv_id
            micros = kwargs.get(micros_var_name, None)
            if micros is not None:
                _check_currency(user_id, conv_id, customer_id, local_currency)

            return f(
                *args,
                **kwargs,
            )

        wrapper.__signature__ = new_sig  # type: ignore[attr-defined]

        return wrapper

    return decorator


@add_currency_check(micros_var_name="budget_amount_micros")
def create_campaign(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    name: Annotated[str, "The name of the campaign"],
    budget_amount_micros: Annotated[int, budget_amount_micros_description],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    context: Context,
    *,
    status: Annotated[
        Optional[Literal["ENABLED", "PAUSED"]],
        "The status of the campaign (ENABLED or PAUSED)",
    ] = None,
    network_settings_target_google_search: Annotated[
        Optional[bool], "Whether ads will be served with google.com search results."
    ] = None,
    network_settings_target_search_network: Annotated[
        Optional[bool],
        "Whether ads will be served on partner sites in the Google Search Network (requires network_settings_target_google_search to also be true).",
    ] = None,
    network_settings_target_content_network: Annotated[
        Optional[bool],
        "Whether ads will be served on specified placements in the Google Display Network. Placements are specified using the Placement criterion.",
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list

    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=Campaign(
            customer_id=customer_id,
            name=name,
            budget_amount_micros=budget_amount_micros,
            status=status,
            network_settings_target_google_search=network_settings_target_google_search,
            network_settings_target_search_network=network_settings_target_search_network,
            network_settings_target_content_network=network_settings_target_content_network,
        ),
        endpoint="/create-campaign",
    )


create_keyword_for_ad_group_description = f"Creates (regular and negative) keywords for Ad Group (AdGroupCriterion). {MODIFICATION_WARNING}"


@add_currency_check()
def create_keyword_for_ad_group(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    ad_group_id: Annotated[str, properties_config["ad_group_id"]["description"]],
    keyword_text: Annotated[str, properties_config["keyword_text"]["description"]],
    keyword_match_type: Annotated[
        str, properties_config["keyword_match_type"]["description"]
    ],
    context: Context,
    *,
    status: Annotated[
        Optional[Literal["ENABLED", "PAUSED"]],
        "The status of the keyword (ENABLED or PAUSED)",
    ] = None,
    negative: Annotated[
        Optional[bool], "Whether to target (false) or exclude (true) the criterion"
    ] = None,
    bid_modifier: Annotated[
        Optional[float], "The modifier for the bids when the criterion matches."
    ] = None,
    cpc_bid_micros: Annotated[
        Optional[int], properties_config["cpc_bid_micros"]["description"]
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list
    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=AdGroupCriterion(
            customer_id=customer_id,
            ad_group_id=ad_group_id,
            status=status,
            keyword_match_type=keyword_match_type,
            keyword_text=keyword_text,
            negative=negative,
            bid_modifier=bid_modifier,
            cpc_bid_micros=cpc_bid_micros,
        ),
        endpoint="/add-keywords-to-ad-group",
    )


update_ad_group_ad_description = f"Update Google Ad. {MODIFICATION_WARNING}"


@add_currency_check()
def update_ad_group_ad(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    ad_group_id: Annotated[str, properties_config["ad_group_id"]["description"]],
    ad_id: Annotated[str, properties_config["ad_id"]["description"]],
    context: Context,
    *,
    status: Annotated[
        Optional[Literal["ENABLED", "PAUSED"]],
        "The status of the Ad (ENABLED or PAUSED)",
    ] = None,
    cpc_bid_micros: Annotated[
        Optional[int], properties_config["cpc_bid_micros"]["description"]
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list
    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=AdGroupAd(
            customer_id=customer_id,
            ad_group_id=ad_group_id,
            ad_id=ad_id,
            cpc_bid_micros=cpc_bid_micros,
            status=status,
            headlines=None,
            descriptions=None,
        ),
        endpoint="/update-ad-group-ad",
    )


update_ad_group_description = f"Update Google Ads Ad Group. {MODIFICATION_WARNING}"


@add_currency_check()
def update_ad_group(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    ad_group_id: Annotated[str, properties_config["ad_group_id"]["description"]],
    context: Context,
    *,
    name: Annotated[Optional[str], "The name of the Ad Group"] = None,
    status: Annotated[
        Optional[Literal["ENABLED", "PAUSED"]],
        "The status of the Ad Group (ENABLED or PAUSED)",
    ] = None,
    cpc_bid_micros: Annotated[
        Optional[int], properties_config["cpc_bid_micros"]["description"]
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list
    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=AdGroup(
            customer_id=customer_id,
            ad_group_id=ad_group_id,
            name=name,
            cpc_bid_micros=cpc_bid_micros,
            status=status,
        ),
        endpoint="/update-ad-group",
    )


create_ad_group_description = f"Create Google Ads Ad Group. {MODIFICATION_WARNING}"


@add_currency_check()
def create_ad_group(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    campaign_id: Annotated[str, properties_config["campaign_id"]["description"]],
    context: Context,
    *,
    name: Annotated[Optional[str], "The name of the Ad Group"] = None,
    status: Annotated[
        Optional[Literal["ENABLED", "PAUSED"]],
        "The status of the Ad group (ENABLED or PAUSED)",
    ] = None,
    cpc_bid_micros: Annotated[
        Optional[int], properties_config["cpc_bid_micros"]["description"]
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list
    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=AdGroup(
            customer_id=customer_id,
            campaign_id=campaign_id,
            name=name,
            cpc_bid_micros=cpc_bid_micros,
            status=status,
        ),
        endpoint="/create-ad-group",
    )


ad_group_criterion_description = (
    f"Update Google Ads Group Criterion. {MODIFICATION_WARNING}"
)


@add_currency_check()
def update_ad_group_criterion(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    ad_group_id: Annotated[str, properties_config["ad_group_id"]["description"]],
    criterion_id: Annotated[str, "Id of the Ad group criterion"],
    context: Context,
    *,
    status: Annotated[
        Optional[Literal["ENABLED", "PAUSED"]],
        "The status of the keyword (ENABLED or PAUSED)",
    ] = None,
    cpc_bid_micros: Annotated[
        Optional[int], properties_config["cpc_bid_micros"]["description"]
    ] = None,
    keyword_text: Annotated[
        Optional[str], properties_config["keyword_text"]["description"]
    ] = None,
    keyword_match_type: Annotated[
        Optional[str], properties_config["keyword_match_type"]["description"]
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list
    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=AdGroupCriterion(
            customer_id=customer_id,
            ad_group_id=ad_group_id,
            criterion_id=criterion_id,
            status=status,
            cpc_bid_micros=cpc_bid_micros,
            keyword_text=keyword_text,
            keyword_match_type=keyword_match_type,
        ),
        endpoint="/update-ad-group-criterion",
    )


update_ad_copy_description = f"""Updates existing Google Ads Ad Copy.
Use 'update_existing_headline_index' if you want to modify existing headline and/or 'update_existing_description_index' to modify existing description.
{MODIFICATION_WARNING}"""

update_existing_headline_index_description = """Index in the headlines list which needs to be updated. Index starts from 0.
Use this parameter ONLY when you want to modify existing headline!"""

update_existing_headline_index_description_description = """Index in the descriptions list which needs to be updated. Index starts from 0.
Use this parameter ONLY when you want to modify existing description!"""


def update_ad_copy(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    ad_id: Annotated[str, properties_config["ad_id"]["description"]],
    context: Context,
    *,
    headline: Annotated[
        Optional[str], properties_config["headline"]["description"]
    ] = None,
    description: Annotated[
        Optional[str], properties_config["description"]["description"]
    ] = None,
    update_existing_headline_index: Annotated[
        Optional[str], update_existing_headline_index_description
    ] = None,
    update_existing_description_index: Annotated[
        Optional[str], update_existing_headline_index_description_description
    ] = None,
    final_url: Annotated[
        Optional[str], properties_config["final_url"]["description"]
    ] = None,
    final_mobile_urls: Annotated[Optional[str], "Ad Copy final_mobile_urls"] = None,
    path1: Annotated[Optional[str], properties_config["path1"]["description"]] = None,
    path2: Annotated[Optional[str], properties_config["path2"]["description"]] = None,
) -> Union[Dict[str, Any], str]:
    if headline and not update_existing_headline_index:
        raise ValueError(
            "If you want to update existing headline, you must specify update_existing_headline_index"
        )
    if description and not update_existing_description_index:
        raise ValueError(
            "If you want to update existing description, you must specify update_existing_description_index"
        )

    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list
    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=AdCopy(
            customer_id=customer_id,
            ad_id=ad_id,
            headline=headline,
            description=description,
            update_existing_headline_index=update_existing_headline_index,
            update_existing_description_index=update_existing_description_index,
            final_url=final_url,
            final_mobile_urls=final_mobile_urls,
            path1=path1,
            path2=path2,
        ),
        endpoint="/create-update-ad-copy",
    )


update_campaign_description = f"Update Google Ads Campaign. {MODIFICATION_WARNING}"


def update_campaign(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    campaign_id: Annotated[str, properties_config["campaign_id"]["description"]],
    context: Context,
    *,
    name: Annotated[Optional[str], "The name of the campaign"] = None,
    status: Annotated[
        Optional[Literal["ENABLED", "PAUSED"]],
        "The status of the campaign (ENABLED or PAUSED)",
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list

    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=Campaign(
            customer_id=customer_id,
            campaign_id=campaign_id,
            name=name,
            status=status,
        ),
        endpoint="/update-campaign",
    )


create_ad_copy_headline_or_description_description = f"""Create NEW headline and/or description in the the Google Ads Copy.
This method does NOT create new Ad Copy, it only creates new headlines and/or descriptions for the existing Ad Copy.
This method should NOT be used for updating existing headlines or descriptions.
{MODIFICATION_WARNING}"""


def create_ad_copy_headline_or_description(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    ad_id: Annotated[str, properties_config["ad_id"]["description"]],
    context: Context,
    *,
    headline: Annotated[
        Optional[str], properties_config["headline"]["description"]
    ] = None,
    description: Annotated[
        Optional[str], properties_config["description"]["description"]
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list
    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=AdCopy(
            customer_id=customer_id,
            ad_id=ad_id,
            headline=headline,
            description=description,
            update_existing_headline_index=None,
            update_existing_description_index=None,
            final_url=None,
            final_mobile_urls=None,
            path1=None,
            path2=None,
        ),
        endpoint="/create-update-ad-copy",
    )


create_ad_group_ad_description = f"""Create Google Ads Ad.
It is not mandatory but it is recommended to use (Display) path1 and path2 parameters.
Use this method only when the client approves the creation of the new Ad, ALL the headlines, descriptions and final_url.
{MODIFICATION_WARNING}"""


def create_ad_group_ad(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    ad_group_id: Annotated[str, properties_config["ad_group_id"]["description"]],
    headlines: Annotated[
        List[str],
        "List of headlines, MINIMUM 3, MAXIMUM 15 headlines. Each headline MUST be LESS than 30 characters!",
    ],
    descriptions: Annotated[
        List[str],
        "List of descriptions, MINIMUM 2, MAXIMUM 4 descriptions. Each description MUST be LESS than 90 characters!",
    ],
    final_url: Annotated[str, properties_config["final_url"]["description"]],
    context: Context,
    *,
    status: Annotated[
        Optional[Literal["ENABLED", "PAUSED"]],
        "The status of the Ad (ENABLED or PAUSED)",
    ] = None,
    path1: Annotated[Optional[str], properties_config["path1"]["description"]] = None,
    path2: Annotated[Optional[str], properties_config["path2"]["description"]] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list

    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=AdGroupAd(
            customer_id=customer_id,
            ad_group_id=ad_group_id,
            status=status,
            headlines=headlines,
            descriptions=descriptions,
            final_url=final_url,
            path1=path1,
            path2=path2,
        ),
        endpoint="/create-ad-group-ad",
    )


create_geo_targeting_for_campaign_description = f"""Creates geographical targeting on the campaign level.
When the client provides the location names (country/city/region), use the 'location_names' parameter without the 'location_ids' parameter. By doing so, you will receive a list of available locations and their IDs.
Once the client approves the locations, you can use the 'location_ids' parameter to create the geo targeting for the campaign.
location_ids and location_names parameters are mutually exclusive and they can NOT be set to None at the same time.
{MODIFICATION_WARNING}"""


def create_geo_targeting_for_campaign(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    campaign_id: Annotated[str, properties_config["campaign_id"]["description"]],
    context: Context,
    *,
    negative: Annotated[
        Optional[bool],
        "Whether to target (False) or exclude (True) the criterion. Default is False.",
    ] = None,
    location_names: Annotated[
        Optional[List[str]],
        "A list of location names e.g. ['Croaita', 'Zagreb']. These values MUST be provided by the client, do NOT improvise!",
    ] = None,
    location_ids: Annotated[Optional[List[str]], "A list of location IDs"] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list
    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=GeoTargetCriterion(
            customer_id=customer_id,
            campaign_id=campaign_id,
            location_names=location_names,
            location_ids=location_ids,
            negative=negative,
        ),
        endpoint="/create-geo-targeting-for-campaign",
    )


create_negative_keyword_for_campaign_description = (
    f"Creates Negative campaign keywords (CampaignCriterion). {MODIFICATION_WARNING}"
)


def create_negative_keyword_for_campaign(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    campaign_id: Annotated[str, properties_config["campaign_id"]["description"]],
    keyword_text: Annotated[str, properties_config["keyword_text"]["description"]],
    keyword_match_type: Annotated[
        str, properties_config["keyword_match_type"]["description"]
    ],
    context: Context,
    *,
    status: Annotated[
        Optional[Literal["ENABLED", "PAUSED"]],
        "The status of the keyword (ENABLED or PAUSED)",
    ] = None,
    negative: Annotated[
        Optional[bool], "Whether to target (false) or exclude (true) the criterion"
    ] = None,
    bid_modifier: Annotated[
        Optional[float], "The modifier for the bids when the criterion matches."
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list

    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=CampaignCriterion(
            customer_id=customer_id,
            campaign_id=campaign_id,
            status=status,
            keyword_match_type=keyword_match_type,
            keyword_text=keyword_text,
            negative=negative,
            bid_modifier=bid_modifier,
        ),
        endpoint="/add-negative-keywords-to-campaign",
    )


remove_google_ads_resource_description = (
    f"Removes the google ads resource. {MODIFICATION_WARNING}"
)

resource_type_description = """One of the following:
Literal['campaign', 'ad_group', 'ad', 'ad_group_criterion', 'campaign_criterion']"""

parent_id_description = """Id of the parent resource, campaign and ad group do not have parent,
ad and ad_group_criterion uses uses ad_group_id, campaign_criterion uses campaign_id"""


def remove_google_ads_resource(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    resource_id: Annotated[str, "Id of the resource which will be removed"],
    resource_type: Annotated[str, resource_type_description],
    context: Context,
    *,
    parent_id: Annotated[Optional[str], parent_id_description] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list

    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=RemoveResource(
            customer_id=customer_id,
            resource_id=resource_id,
            resource_type=resource_type,
            parent_id=parent_id,
        ),
        endpoint="/remove-google-ads-resource",
    )


remove_ad_copy_headline_or_description_description = f"""Removes existing Google Ads Ad Copy headline or/and description.
Use 'update_existing_headline_index' if you want to remove existing headline and/or 'update_existing_description_index' to remove existing description.
{MODIFICATION_WARNING}"""


def remove_ad_copy_headline_or_description(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    ad_id: Annotated[str, properties_config["ad_id"]["description"]],
    context: Context,
    *,
    update_existing_headline_index: Annotated[
        Optional[str],
        "Index in the headlines list which needs to be removed. Index starts from 0.",
    ] = None,
    update_existing_description_index: Annotated[
        Optional[str],
        "Index in the descriptions list which needs to be removed. Index starts from 0.",
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list

    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=AdCopy(
            customer_id=customer_id,
            ad_id=ad_id,
            headline=None,
            description=None,
            update_existing_headline_index=update_existing_headline_index,
            update_existing_description_index=update_existing_description_index,
            final_url=None,
            final_mobile_urls=None,
        ),
        endpoint="/create-update-ad-copy",
    )


update_campaigns_negative_keywords_description = (
    f"Update the Google Ads keywords (on campaign level). {MODIFICATION_WARNING}"
)


def update_campaigns_negative_keywords(
    customer_id: Annotated[str, properties_config["customer_id"]["description"]],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]["description"]
    ],
    modification_question: Annotated[
        str, properties_config["modification_question"]["description"]
    ],
    campaign_id: Annotated[str, properties_config["campaign_id"]["description"]],
    criterion_id: Annotated[str, "Id of the Campaign criterion"],
    context: Context,
    *,
    keyword_text: Annotated[
        Optional[str], properties_config["keyword_text"]["description"]
    ] = None,
    keyword_match_type: Annotated[
        Optional[str], properties_config["keyword_match_type"]["description"]
    ] = None,
) -> Union[Dict[str, Any], str]:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list
    return google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=CampaignCriterion(
            customer_id=customer_id,
            campaign_id=campaign_id,
            criterion_id=criterion_id,
            keyword_text=keyword_text,
            keyword_match_type=keyword_match_type,
        ),
        endpoint="/update-campaigns-negative-keywords",
    )


def add_shared_functions(toolbox: Toolbox) -> None:
    toolbox.add_function(reply_to_client_2_description)(reply_to_client_2)
    toolbox.add_function(
        description=ask_client_for_permission_description,
    )(ask_client_for_permission)
    toolbox.add_function(get_info_from_the_web_page_description)(
        get_info_from_the_web_page
    )
    toolbox.add_function(change_google_account_description)(change_google_account)
    toolbox.add_function(list_accessible_customers_description)(
        list_accessible_customers
    )
    toolbox.add_function(execute_query_description)(execute_query)
    toolbox.add_function(create_campaign_description)(create_campaign)


def create_google_ads_team_toolbox(
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[str, Optional[str]]],
) -> Toolbox:
    toolbox = Toolbox()

    context = Context(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
    )
    toolbox.set_context(context)

    add_shared_functions(toolbox)

    toolbox.add_function(create_keyword_for_ad_group_description)(
        create_keyword_for_ad_group
    )
    toolbox.add_function(update_ad_group_ad_description)(update_ad_group_ad)
    toolbox.add_function(update_ad_group_description)(update_ad_group)
    toolbox.add_function(create_ad_group_description)(create_ad_group)
    toolbox.add_function(ad_group_criterion_description)(update_ad_group_criterion)
    toolbox.add_function(update_ad_copy_description)(update_ad_copy)
    toolbox.add_function(update_campaign_description)(update_campaign)
    toolbox.add_function(create_ad_copy_headline_or_description_description)(
        create_ad_copy_headline_or_description
    )
    toolbox.add_function(create_ad_group_ad_description)(create_ad_group_ad)
    toolbox.add_function(create_geo_targeting_for_campaign_description)(
        create_geo_targeting_for_campaign
    )
    toolbox.add_function(create_negative_keyword_for_campaign_description)(
        create_negative_keyword_for_campaign
    )
    toolbox.add_function(remove_google_ads_resource_description)(
        remove_google_ads_resource
    )
    toolbox.add_function(remove_ad_copy_headline_or_description_description)(
        remove_ad_copy_headline_or_description
    )
    toolbox.add_function(update_campaigns_negative_keywords_description)(
        update_campaigns_negative_keywords
    )

    return toolbox
