import ast
import inspect
from functools import wraps
from typing import Annotated, Any, Callable, Dict, List, Literal, Optional, Tuple, Union

from google_ads.model import Campaign

from ....google_ads.client import execute_query as execute_query_client
from ....google_ads.client import get_login_url, google_ads_create_update
from ....google_ads.client import (
    list_accessible_customers as list_accessible_customers_client,
)
from ..toolboxes import Toolbox
from ._function_configs import MODIFICATION_WARNING, properties_config
from ._functions import (
    Context,
    ask_client_for_permission,
    ask_client_for_permission_description,
    ask_client_for_permission_with_context,
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

    return list_accessible_customers_client(user_id=user_id, conv_id=conv_id)


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
                annotation=Annotated[Optional[str], "local currency"],
                default=None,
            )
        )
        new_sig = sig.replace(parameters=params)

        @wraps(f)
        def wrapper(
            *args: Any,
            local_currency: Annotated[Optional[str], "local currency"] = None,
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


def add_shared_functions(toolbox: Toolbox) -> None:
    toolbox.add_function(reply_to_client_2_description)(reply_to_client_2)
    toolbox.add_function(
        description=ask_client_for_permission_description,
        name=ask_client_for_permission.__name__,
    )(ask_client_for_permission_with_context)
    toolbox.add_function(get_info_from_the_web_page_description)(
        get_info_from_the_web_page
    )
    toolbox.add_function(change_google_account_description)(change_google_account)
    toolbox.add_function(list_accessible_customers_description)(
        list_accessible_customers
    )
    toolbox.add_function(execute_query_description)(execute_query)

    # todo: wrap with add_currency_check
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

    return toolbox
