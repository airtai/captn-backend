import json
import urllib.parse
import uuid
from os import environ
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
import pandas as pd
from asyncer import asyncify
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.v17.common.types.criteria import LanguageInfo
from google.api_core import protobuf_helpers
from google.auth.exceptions import RefreshError
from google.protobuf import json_format

from captn.captn_agents.helpers import get_db_connection, get_wasp_db_url

from .model import (
    AdBase,
    AdCopy,
    AddPageFeedItems,
    AdGroup,
    AdGroupAd,
    AdGroupCriterion,
    Campaign,
    CampaignCallouts,
    CampaignCriterion,
    CampaignLanguageCriterion,
    CampaignSharedSet,
    Criterion,
    ExistingCampaignSitelinks,
    GeoTargetCriterion,
    NewCampaignSitelinks,
    RemoveResource,
)

router = APIRouter()

# Load client secret data from the JSON file
with open("client_secret.json") as secret_file:
    client_secret_data = json.load(secret_file)

# OAuth2 configuration
oauth2_settings = {
    "auth_uri": client_secret_data["web"]["auth_uri"],
    "tokenUrl": client_secret_data["web"]["token_uri"],
    "clientId": client_secret_data["web"]["client_id"],
    "clientSecret": client_secret_data["web"]["client_secret"],
    "redirectUri": client_secret_data["web"]["redirect_uris"][0],
}


async def get_users(day_of_week_created: Optional[str] = None) -> Any:
    wasp_db_url = await get_wasp_db_url()
    if day_of_week_created:
        query = f"""SELECT * FROM "User"
WHERE TRIM(TO_CHAR("createdAt", 'Day')) = '{day_of_week_created}'"""  # nosec: [B608]
    else:
        query = 'SELECT * from "User"'
    async with get_db_connection(db_url=wasp_db_url) as db:
        users = await db.query_raw(query)

    return users


async def get_user(user_id: Union[int, str]) -> Any:
    wasp_db_url = await get_wasp_db_url()
    async with get_db_connection(db_url=wasp_db_url) as db:
        user = await db.query_first(
            f'SELECT * from "User" where id={user_id}'  # nosec: [B608]
        )
    if not user:
        raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")
    return user


# async def get_user_id_chat_id_from_conversation(
#     conv_id: Union[int, str]
# ) -> Tuple[Any, Any]:
#     wasp_db_url = await get_wasp_db_url()
#     async with get_db_connection(db_url=wasp_db_url) as db:  # type: ignore[var-annotated]
#         conversation = await db.query_first(
#             f'SELECT * from "Conversation" where id={conv_id}'  # nosec: [B608]
#         )
#         if not conversation:
#             raise HTTPException(status_code=404, detail=f"conv_id {conv_id} not found")
#     user_id = conversation["userId"]
#     chat_id = conversation["chatId"]
#     return user_id, chat_id


async def get_user_id_chat_uuid_from_chat_id(
    chat_id: Union[int, str],
) -> Tuple[int, str]:
    wasp_db_url = await get_wasp_db_url()
    async with get_db_connection(db_url=wasp_db_url) as db:
        chat = await db.query_first(
            f'SELECT * from "Chat" where id={chat_id}'  # nosec: [B608]
        )
        if not chat:
            raise HTTPException(status_code=404, detail=f"chat {chat} not found")
    user_id = chat["userId"]
    chat_uuid = chat["uuid"]
    return user_id, chat_uuid


@router.get("/user-id-chat-uuid")
async def get_chat_uuid_from_chat_id(
    chat_id: Union[int, str],
) -> str:
    _, chat_uuid = await get_user_id_chat_uuid_from_chat_id(chat_id)
    return chat_uuid


async def is_authenticated_for_ads(user_id: int) -> bool:
    await get_user(user_id=user_id)
    async with get_db_connection() as db:
        data = await db.gauth.find_unique(where={"user_id": user_id})

    if not data:
        return False
    return True


# Route 1: Redirect to Google OAuth
@router.get("/login")
async def get_login_url(
    request: Request,
    user_id: int = Query(title="User ID"),
    conv_id: int = Query(title="Conversation ID"),
    force_new_login: bool = Query(title="Force new login", default=False),
) -> Dict[str, str]:
    if not force_new_login:
        is_authenticated = await is_authenticated_for_ads(user_id=user_id)
        if is_authenticated:
            return {"login_url": "User is already authenticated"}

    google_oauth_url = (
        f"{oauth2_settings['auth_uri']}?client_id={oauth2_settings['clientId']}"
        f"&redirect_uri={oauth2_settings['redirectUri']}&response_type=code"
        f"&scope={urllib.parse.quote_plus('https://www.googleapis.com/auth/adwords email')}"
        f"&access_type=offline&prompt=consent&state={conv_id}"
        # f"&access_type=offline&prompt=consent&state={chat_id}"
    )
    markdown_url = f"To navigate Google Ads waters, I require access to your account. Please [click here]({google_oauth_url}) to grant permission."
    return {"login_url": markdown_url}


# Route 2: Save user credentials/token to a JSON file
@router.get("/login/callback")
async def login_callback(
    code: str = Query(title="Authorization Code"), state: str = Query(title="State")
) -> RedirectResponse:
    chat_id = state
    user_id, chat_uuid = await get_user_id_chat_uuid_from_chat_id(chat_id)
    # user_id, chat_id = await get_user_id_chat_id_from_conversation(conv_id)
    user = await get_user(user_id=user_id)

    token_request_data = {
        "code": code,
        "client_id": oauth2_settings["clientId"],
        "client_secret": oauth2_settings["clientSecret"],
        "redirect_uri": oauth2_settings["redirectUri"],
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:  # nosec [B113]
        response = await client.post(
            oauth2_settings["tokenUrl"], data=token_request_data
        )

    if response.status_code == 200:
        token_data = response.json()

    async with httpx.AsyncClient() as client:  # nosec [B113]
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )

    if userinfo_response.status_code == 200:
        user_info = userinfo_response.json()
    async with get_db_connection() as db:
        await db.gauth.upsert(
            where={"user_id": user["id"]},
            data={
                "create": {
                    "user_id": user["id"],
                    "creds": json.dumps(token_data),
                    "info": json.dumps(user_info),
                },
                "update": {
                    "creds": json.dumps(token_data),
                    "info": json.dumps(user_info),
                },
            },
        )

    # async with get_db_connection() as db:  # type: ignore[var-annotated]
    #     task: Task = await db.task.find_unique_or_raise(where={"team_id": int(conv_id)})
    redirect_domain = environ.get("REDIRECT_DOMAIN", "https://captn.ai")
    logged_in_message = "I have successfully logged in"
    # redirect_uri = f"{redirect_domain}/chat/{chat_id}?msg={logged_in_message}&team_id={task.team_id}&team_name={task.team_name}"
    redirect_uri = f"{redirect_domain}/chat/{chat_uuid}?msg={logged_in_message}"
    return RedirectResponse(redirect_uri)


async def load_user_credentials(user_id: Union[int, str]) -> Any:
    await get_user(user_id=user_id)
    async with get_db_connection() as db:
        data = await db.gauth.find_unique_or_raise(where={"user_id": user_id})

    return data.creds


# Initialize Google Ads API client
async def create_google_ads_client(
    user_id: int,
    user_credentials: Dict[str, Any],
    login_customer_id: Optional[str],
    use_proto_plus: bool = False,
) -> GoogleAdsClient:
    # Create a dictionary with the required structure for GoogleAdsClient
    google_ads_credentials = {
        "developer_token": environ.get("DEVELOPER_TOKEN"),
        "use_proto_plus": use_proto_plus,
        "client_id": oauth2_settings["clientId"],
        "client_secret": oauth2_settings["clientSecret"],
        "refresh_token": user_credentials["refresh_token"],
    }
    if login_customer_id:
        google_ads_credentials["login_customer_id"] = login_customer_id

    # Initialize the Google Ads API client with the properly structured dictionary
    try:
        client = GoogleAdsClient.load_from_dict(google_ads_credentials)
    except RefreshError:
        # Something is wrong with the credentials, delete them from the database so they can be re-generated
        async with get_db_connection() as db:
            await db.gauth.delete(where={"user_id": user_id})

        raise HTTPException(  # noqa
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Please try to execute the command again.",
        )

    return client


async def _check_if_customer_id_is_manager_or_exception_is_raised(
    user_id: int, customer_id: str
) -> bool:
    query = (
        "SELECT customer.id, customer.descriptive_name, customer.manager, customer.test_account "
        "FROM customer_client"
    )

    try:
        customer = await search(
            user_id=user_id, customer_ids=[customer_id], query=query
        )

        for result in customer.values():
            is_manager = result[0]["customer"]["manager"]
            if not is_manager:
                return False
    except Exception as e:
        print(
            f"Skipping the following customer_id: {customer_id}, user_id: {user_id} because of the exception:\n{e}"
        )
    return True


# Route 3: List accessible customer ids
@router.get("/list-accessible-customers")
async def list_accessible_customers(
    user_id: int = Query(title="User ID"),
    get_only_non_manager_accounts: bool = Query(title="Only non manager accounts"),
) -> List[str]:
    try:
        user_credentials = await load_user_credentials(user_id)
        client = await create_google_ads_client(
            user_id=user_id, user_credentials=user_credentials, login_customer_id=None
        )
        customer_service = client.get_service("CustomerService")
        accessible_customers = await asyncify(
            customer_service.list_accessible_customers
        )()

        customer_ids = [x.split("/")[-1] for x in accessible_customers.resource_names]
        if len(customer_ids) == 0 or not get_only_non_manager_accounts:
            return customer_ids

        # Return only non Manager accounts!
        non_manager_customer_ids = []

        for customer_id in customer_ids:
            skip_customer = (
                await _check_if_customer_id_is_manager_or_exception_is_raised(
                    user_id=user_id, customer_id=customer_id
                )
            )
            if not skip_customer:
                non_manager_customer_ids.append(customer_id)
        return non_manager_customer_ids

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


# Route 4: Fetch user's ad campaign data
@router.get("/search")
async def search(
    user_id: int = Query(title="User ID"),
    customer_ids: List[str] = Query(None),  # noqa
    query: str = Query(None, title="Google ads query"),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> Dict[str, List[Any]]:
    user_credentials = await load_user_credentials(user_id)
    client = await create_google_ads_client(
        user_id=user_id,
        user_credentials=user_credentials,
        login_customer_id=login_customer_id,
    )
    service = client.get_service("GoogleAdsService")

    # Replace this with your actual Google Ads API query to fetch campaign data
    if not query:
        query = (
            "SELECT campaign.id, campaign.name, ad_group.id, ad_group.name "
            "FROM keyword_view WHERE segments.date DURING LAST_7_DAYS"
        )
    print(f"{query=}")

    if not customer_ids:
        customer_ids = await list_accessible_customers(user_id=user_id)
    print(f"{customer_ids=}")

    campaign_data = {}

    try:
        for customer_id in customer_ids:
            # try:
            response = await asyncify(service.search)(
                customer_id=customer_id, query=query
            )
            l = []  # noqa
            for row in response:
                json_str = json_format.MessageToJson(row)
                l.append(json.loads(json_str))
            campaign_data[customer_id] = l
            # except GoogleAdsException:
            #     print(f"Exception for {customer_id}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

    return campaign_data


@router.get("/list-accessible-customers-with-account-types")
async def list_accessible_customers_with_account_types(
    user_id: int = Query(title="User ID"),
) -> Dict[str, Any]:
    customers_ids = await list_accessible_customers(
        user_id=user_id, get_only_non_manager_accounts=False
    )

    query = """
SELECT
    customer_client.manager,
    customer_client.descriptive_name,
    customer_client.id
FROM
    customer_client
WHERE
    customer_client.status = 'ENABLED'
"""

    search_results = {}
    for customer_id in customers_ids:
        try:
            search_result = await search(
                user_id=user_id,
                customer_ids=[customer_id],
                query=query,
                login_customer_id=customer_id,
            )
        except Exception as e:
            # usually happens when the customer isn't enabled or is deactivated
            print(f"Exception for {customer_id}: {e}")
            continue
        search_result_customer = [
            customer
            for customer in search_result[customer_id]
            if customer["customerClient"]["id"] == customer_id
        ]
        search_results[customer_id] = search_result_customer
    return search_results


# Route 5: Fetch user's emails
@router.get("/get-user-ids-and-emails")
async def get_user_ids_and_emails(day_of_week_created: Optional[str] = None) -> str:
    users = await get_users(day_of_week_created=day_of_week_created)
    id_email_dict = {user["id"]: user["email"] for user in users}
    return json.dumps(id_email_dict)


AVALIABLE_KEYS = ["campaign", "ad_group", "ad_group_ad", "ad_group_criterion"]


async def _get_client(
    user_id: int, login_customer_id: Optional[str]
) -> GoogleAdsClient:
    user_credentials = await load_user_credentials(user_id)
    client = await create_google_ads_client(
        user_id=user_id,
        user_credentials=user_credentials,
        use_proto_plus=True,
        login_customer_id=login_customer_id,
    )
    return client


def _retrieve_field_mask(
    client: GoogleAdsClient,
    operation: Any,
    operation_update: Any,
) -> None:
    # Retrieve a FieldMask for the fields configured in the campaign/ad_group/ad_group_ad.
    client.copy_from(
        operation.update_mask,
        protobuf_helpers.field_mask(None, operation_update._pb),  # type: ignore[no-untyped-call]
    )


async def _set_fields(
    client: GoogleAdsClient,
    model_or_dict: Dict[str, Any],
    operation: Any,
    operation_update: Any,
    user_id: int,
) -> None:
    for attribute_name, attribute_value in model_or_dict.items():
        if attribute_value is not None:
            setattr(operation_update, attribute_name, attribute_value)

    _retrieve_field_mask(
        client=client, operation=operation, operation_update=operation_update
    )


MAX_HEADLINES_OR_DESCRIPTIONS = {
    "headlines": 15,
    "descriptions": 4,
}
MAX_HEADLINES_OR_DESCRIPTIONS_ERROR_MSG = "There is already maximum number of"


def _set_headline_or_description(
    client: GoogleAdsClient,
    operation_update: Any,
    update_field: str,
    new_text: Optional[str],
    update_existing_index: Optional[int],
    responsive_search_ad: Dict[str, Any],
) -> None:
    updated_fields = []

    for head_or_desc in responsive_search_ad[update_field]:
        text = head_or_desc["text"]
        headline_or_description = client.get_type("AdTextAsset")
        headline_or_description.text = text
        updated_fields.append(headline_or_description)

    if update_existing_index is not None:
        if new_text:
            # update headline or description
            updated_fields[update_existing_index].text = new_text
        else:
            # delete headline or description
            updated_fields.pop(update_existing_index)
    else:
        if len(updated_fields) >= MAX_HEADLINES_OR_DESCRIPTIONS[update_field]:
            raise ValueError(
                f"{MAX_HEADLINES_OR_DESCRIPTIONS_ERROR_MSG} {update_field}: {len(updated_fields)}"
            )
        headline_or_description = client.get_type("AdTextAsset")
        headline_or_description.text = new_text
        updated_fields.append(headline_or_description)

    getattr(operation_update.responsive_search_ad, update_field).extend(updated_fields)


def _update_ad_copy_display_path(
    operation_create_update_responsive_search_ad: Any,
    path1: Optional[str],
    path2: Optional[str],
) -> None:
    print(f"{path1=}, {path2=}")
    if path1 is not None:
        operation_create_update_responsive_search_ad.path1 = (
            path1 if path1 != "" else " "
        )
    if path2 is not None:
        if path2 == "":
            operation_create_update_responsive_search_ad.path2 = " "
            return

        if (path1 is None or path1 == "") and path2:
            raise ValueError("Field path2 can only be set when path1 is also set!")
        operation_create_update_responsive_search_ad.path2 = path2


async def _set_fields_ad_copy(
    client: GoogleAdsClient,
    model_or_dict: AdCopy,
    operation: Any,
    operation_update: Any,
    user_id: int,
) -> None:
    # for attribute_name, attribute_value in model_dict.items():
    #     if attribute_value is not None:
    #         setattr(operation_update, attribute_name, attribute_value)

    modify_headlines = (
        model_or_dict.headline
        or model_or_dict.update_existing_headline_index is not None
    )
    modify_descriptions = (
        model_or_dict.description
        or model_or_dict.update_existing_description_index is not None
    )

    if modify_headlines or modify_descriptions:
        query = f"""SELECT ad_group_ad.ad.responsive_search_ad.headlines, ad_group_ad.ad.responsive_search_ad.descriptions
FROM ad_group_ad
WHERE ad_group_ad.ad.id = {model_or_dict.ad_id}"""  # nosec: [B608]
        search_result = await search(
            user_id=user_id, customer_ids=[model_or_dict.customer_id], query=query
        )
        responsive_search_ad = search_result[model_or_dict.customer_id][0]["adGroupAd"][
            "ad"
        ]["responsiveSearchAd"]

        errors = []
        if modify_headlines:
            update_field = "headlines"
            new_text = model_or_dict.headline
            try:
                _set_headline_or_description(
                    client=client,
                    operation_update=operation_update,
                    update_field=update_field,
                    new_text=new_text,
                    update_existing_index=model_or_dict.update_existing_headline_index,
                    responsive_search_ad=responsive_search_ad,
                )
            except ValueError as e:
                errors.append(str(e))

        if modify_descriptions:
            try:
                update_field = "descriptions"
                new_text = model_or_dict.description
                _set_headline_or_description(
                    client=client,
                    operation_update=operation_update,
                    update_field=update_field,
                    new_text=new_text,
                    update_existing_index=model_or_dict.update_existing_description_index,
                    responsive_search_ad=responsive_search_ad,
                )
            except ValueError as e:
                errors.append(str(e))
        if errors:
            raise ValueError("\n".join(errors))

    if model_or_dict.final_url:
        final_url = model_or_dict.final_url
        final_url = (
            final_url if final_url.startswith("http") else f"https://{final_url}"
        )
        operation_update.final_urls.append(final_url)
    if model_or_dict.final_mobile_urls:
        operation_update.final_mobile_urls.append(model_or_dict.final_mobile_urls)

    _update_ad_copy_display_path(
        operation_create_update_responsive_search_ad=operation_update.responsive_search_ad,
        path1=model_or_dict.path1,
        path2=model_or_dict.path2,
    )

    _retrieve_field_mask(
        client=client, operation=operation, operation_update=operation_update
    )


async def _mutate(
    service: Any, mutate_function_name: str, customer_id: str, operation: Any
) -> Any:
    mutate_function = getattr(service, mutate_function_name)
    response = await asyncify(mutate_function)(
        customer_id=customer_id, operations=[operation]
    )
    return response


async def _get_necessary_parameters(
    user_id: int,
    model: AdBase,
    service_operation_and_function_names: Dict[str, Any],
    crud_operation_name: str,
    mandatory_fields: List[str],
    login_customer_id: Optional[str],
) -> Tuple[GoogleAdsClient, Any, Any, Dict[str, Any], str, Any, List[Any]]:
    client = await _get_client(user_id=user_id, login_customer_id=login_customer_id)

    service = client.get_service(service_operation_and_function_names["service"])
    operation = client.get_type(service_operation_and_function_names["operation"])

    model_dict = model.model_dump()

    if "customer_id" in mandatory_fields:
        mandatory_fields.remove("customer_id")
    else:
        raise KeyError("customer_id must be inside the mandatory_fields list")
    customer_id = model_dict.pop("customer_id")

    crud_operation = getattr(operation, crud_operation_name)

    mandatory_fields_values = [
        model_dict.pop(mandatory_field) for mandatory_field in mandatory_fields
    ]

    return (
        client,
        service,
        operation,
        model_dict,
        customer_id,
        crud_operation,
        mandatory_fields_values,
    )


async def _get_existing_ad_group_criterion(
    user_id: int,
    customer_id: str,
    criterion_id: Optional[str],
    login_customer_id: Optional[str],
) -> Any:
    query = f"""SELECT ad_group_criterion.status, ad_group_criterion.negative,
ad_group_criterion.keyword.match_type, ad_group_criterion.keyword.text
FROM ad_group_criterion
WHERE ad_group_criterion.criterion_id = {criterion_id}"""  # nosec: [B608]
    ad_group_criterion = await search(
        user_id=user_id,
        customer_ids=[customer_id],
        query=query,
        login_customer_id=login_customer_id,
    )
    return ad_group_criterion[customer_id][0]["adGroupCriterion"]


async def _update(
    user_id: int,
    model: AdBase,
    service_operation_and_function_names: Dict[str, Any],
    mandatory_fields: List[str],
    login_customer_id: Optional[str],
) -> str:
    (
        client,
        service,
        operation,
        model_dict,
        customer_id,
        operation_update,
        mandatory_fields_values,
    ) = await _get_necessary_parameters(
        user_id=user_id,
        model=model,
        service_operation_and_function_names=service_operation_and_function_names,
        crud_operation_name="update",
        mandatory_fields=mandatory_fields,
        login_customer_id=login_customer_id,
    )

    try:
        service_path_function = getattr(
            service, service_operation_and_function_names["service_path_update_delete"]
        )
        operation_update.resource_name = service_path_function(
            customer_id, *mandatory_fields_values
        )

        model_or_dict = model if isinstance(model, AdCopy) else model_dict
        await service_operation_and_function_names["setattr_update_func"](
            client=client,
            model_or_dict=model_or_dict,
            operation=operation,
            operation_update=operation_update,
            user_id=user_id,
        )

        response = await _mutate(
            service,
            service_operation_and_function_names["mutate"],
            customer_id,
            operation,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    return f"Updated {response.results[0].resource_name}."


def _create_ad_group_setattr(
    model_dict: Dict[str, Any], operation_create: Any, client: Any
) -> None:
    for attribute_name, attribute_value in model_dict.items():
        if attribute_value is not None:
            setattr(operation_create, attribute_name, attribute_value)


def _create_campaign_setattr(
    model_dict: Dict[str, Any], operation_create: Any, client: Any
) -> None:
    for attribute_name, attribute_value in model_dict.items():
        if attribute_value is not None:
            if attribute_name == "manual_cpc":
                operation_create.manual_cpc.enhanced_cpc_enabled = attribute_value
            elif "network_settings" in attribute_name:
                attribute_name = attribute_name.replace("network_settings_", "")
                setattr(
                    operation_create.network_settings, attribute_name, attribute_value
                )
            else:
                setattr(operation_create, attribute_name, attribute_value)

    operation_create.advertising_channel_type = (
        client.enums.AdvertisingChannelTypeEnum.SEARCH
    )

    if not model_dict["manual_cpc"]:
        # The bidding strategy for Maximize Clicks is TargetSpend.
        # The target_spend_micros is deprecated so don't put any value.
        # See other bidding strategies you can select in the link below.
        # https://developers.google.com/google-ads/api/reference/rpc/v11/Campaign#campaign_bidding_strategy
        operation_create.target_spend.target_spend_micros = 0

    # # Optional: Set the start date.
    # start_time = datetime.date.today() + datetime.timedelta(days=1)
    # campaign.start_date = datetime.date.strftime(start_time, _DATE_FORMAT)

    # # Optional: Set the end date.
    # end_time = start_time + datetime.timedelta(weeks=4)
    # campaign.end_date = datetime.date.strftime(end_time, _DATE_FORMAT)


def _keywords_setattr(
    model_dict: Dict[str, Any], operation_create: Any, client: Any
) -> None:
    for attribute_name, attribute_value in model_dict.items():
        if attribute_value is not None:
            if "keyword_" in attribute_name:
                attribute_name = attribute_name.replace("keyword_", "")
                setattr(operation_create.keyword, attribute_name, attribute_value)
            else:
                setattr(operation_create, attribute_name, attribute_value)


def _create_ad_text_asset(client: Any, text: str, pinned_field: str = None) -> Any:  # type: ignore
    """Create an AdTextAsset.
    Args:
        client: an initialized GoogleAdsClient instance.
        text: text for headlines and descriptions.
        pinned_field: to pin a text asset so it always shows in the ad.

    Returns:
        An AdTextAsset.
    """
    ad_text_asset = client.get_type("AdTextAsset")
    ad_text_asset.text = text
    if pinned_field:
        ad_text_asset.pinned_field = pinned_field
    return ad_text_asset


def _create_ad_group_ad_set_attr(
    model_dict: Dict[str, Any], operation_create: Any, client: Any
) -> None:
    print(model_dict)
    if "status" in model_dict:
        operation_create.status = client.enums.AdGroupAdStatusEnum.ENABLED

    # Set responsive search ad info.
    # https://developers.google.com/google-ads/api/reference/rpc/v11/ResponsiveSearchAdInfo

    # The list of possible final URLs after all cross-domain redirects for the ad.
    if "final_url" not in model_dict:
        raise KeyError("Final_urls must be provided for creating an ad!")

    final_url = (
        model_dict["final_url"]
        if model_dict["final_url"].startswith("http")
        else f"https://{model_dict['final_url']}"
    )
    operation_create.ad.final_urls.append(final_url)

    # Set a pinning to always choose this asset for HEADLINE_1. Pinning is
    # optional; if no pinning is set, then headlines and descriptions will be
    # rotated and the ones that perform best will be used more often.
    NUM_HEADLINES_1 = 3
    NUM_HEADLINES_2 = 3
    TOTAL_HEADLINES_1_2 = NUM_HEADLINES_1 + NUM_HEADLINES_2
    num_headlines = len(model_dict["headlines"])
    if num_headlines < NUM_HEADLINES_1:
        raise ValueError(f"Number of headlines must be at least {NUM_HEADLINES_1}.")

    # Pin as first headlines
    headlines = [
        _create_ad_text_asset(
            client, headline, client.enums.ServedAssetFieldTypeEnum.HEADLINE_1
        )
        for headline in model_dict["headlines"][0:NUM_HEADLINES_1]
    ]

    if num_headlines >= NUM_HEADLINES_1 and num_headlines <= TOTAL_HEADLINES_1_2:
        # Pin as second headlines
        headlines += [
            _create_ad_text_asset(
                client, headline, client.enums.ServedAssetFieldTypeEnum.HEADLINE_2
            )
            for headline in model_dict["headlines"][NUM_HEADLINES_1:]
        ]
    else:
        # Pin as second headlines
        headlines += [
            _create_ad_text_asset(
                client, headline, client.enums.ServedAssetFieldTypeEnum.HEADLINE_2
            )
            for headline in model_dict["headlines"][NUM_HEADLINES_1:TOTAL_HEADLINES_1_2]
        ]
        # Don't pin the rest
        headlines += [
            _create_ad_text_asset(client, headline)
            for headline in model_dict["headlines"][TOTAL_HEADLINES_1_2:]
        ]

    operation_create.ad.responsive_search_ad.headlines.extend(headlines)

    # pin first description
    descriptions = [
        _create_ad_text_asset(
            client,
            model_dict["descriptions"][0],
            client.enums.ServedAssetFieldTypeEnum.DESCRIPTION_1,
        )
    ]
    descriptions += [
        _create_ad_text_asset(client, desc) for desc in model_dict["descriptions"][1:]
    ]

    operation_create.ad.responsive_search_ad.descriptions.extend(descriptions)

    _update_ad_copy_display_path(
        operation_create_update_responsive_search_ad=operation_create.ad.responsive_search_ad,
        path1=model_dict["path1"],
        path2=model_dict["path2"],
    )


GOOGLE_ADS_RESOURCE_DICT: Dict[str, Dict[str, Any]] = {
    "campaign": {
        "service": "CampaignService",
        "operation": "CampaignOperation",
        "mutate": "mutate_campaigns",
        "service_path_update_delete": "campaign_path",
        "setattr_create_func": _create_campaign_setattr,
        "setattr_update_func": _set_fields,
    },
    "ad_group": {
        "service": "AdGroupService",
        "operation": "AdGroupOperation",
        "mutate": "mutate_ad_groups",
        "service_path_create": "campaign_path",
        "service_path_update_delete": "ad_group_path",
        "setattr_create_func": _create_ad_group_setattr,
        "setattr_update_func": _set_fields,
    },
    "ad": {
        "service": "AdGroupAdService",
        "operation": "AdGroupAdOperation",
        "mutate": "mutate_ad_group_ads",
        "service_path_create": "ad_group_path",
        "service_path_update_delete": "ad_group_ad_path",
        "setattr_create_func": _create_ad_group_ad_set_attr,
        "setattr_update_func": _set_fields,
    },
    "ad_copy": {
        "service": "AdService",
        "operation": "AdOperation",
        "mutate": "mutate_ads",
        "service_path_update_delete": "ad_path",
        "setattr_update_func": _set_fields_ad_copy,
    },
    "ad_group_criterion": {
        "service": "AdGroupCriterionService",
        "operation": "AdGroupCriterionOperation",
        "mutate": "mutate_ad_group_criteria",
        "service_path_create": "ad_group_path",
        "service_path_update_delete": "ad_group_criterion_path",
        "setattr_create_func": _keywords_setattr,
        "setattr_update_func": _set_fields,
    },
    "campaign_criterion": {
        "service": "CampaignCriterionService",
        "operation": "CampaignCriterionOperation",
        "mutate": "mutate_campaign_criteria",
        "service_path_create": "campaign_path",
        "service_path_update_delete": "campaign_criterion_path",
        "setattr_create_func": _keywords_setattr,
        "setattr_update_func": _set_fields,
    },
    "asset_set_asset": {
        "service": "AssetSetAssetService",
        "operation": "AssetSetAssetOperation",
        "mutate": "mutate_asset_set_assets",
        "service_path_update_delete": "asset_set_asset_path",
    },
}


@router.get("/update-ad-group-ad")
async def update_ad_group_ad(
    user_id: int,
    ad_model: AdGroupAd = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["ad"]

    return await _update(
        user_id=user_id,
        model=ad_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_group_id", "ad_id"],
        login_customer_id=login_customer_id,
    )


def _create_campaign_budget(
    client: Any, customer_id: str, amount_micros: int, explicitly_shared: Optional[bool]
) -> Any:
    """Creates campaign budget resource.

    Args:
      client: an initialized GoogleAdsClient instance.
      customer_id: a client customer ID.

    Returns:
      Campaign budget resource name.
    """
    # Create a budget, which can be shared by multiple campaigns.
    campaign_budget_service = client.get_service("CampaignBudgetService")
    campaign_budget_operation = client.get_type("CampaignBudgetOperation")
    campaign_budget = campaign_budget_operation.create
    campaign_budget.name = f"Campaign budget {uuid.uuid4()}"
    campaign_budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    campaign_budget.amount_micros = amount_micros
    campaign_budget.explicitly_shared = explicitly_shared

    # Add budget.
    campaign_budget_response = campaign_budget_service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[campaign_budget_operation]
    )

    return campaign_budget_response.results[0].resource_name


def get_languages_df() -> pd.DataFrame:
    file_path = Path(__file__).parent / "language_codes.csv"
    return pd.read_csv(file_path)


def _read_avaliable_languages() -> Dict[str, int]:
    language_codes = get_languages_df()
    return dict(
        zip(
            language_codes["Language code"],
            language_codes["Criterion ID"],
            strict=False,
        )
    )


avalible_languages = _read_avaliable_languages()


def get_languages(languages_codes: List[str], negative: bool) -> Dict[str, int]:
    languages_codes = [code.lower().strip() for code in languages_codes]

    # check if the language codes are valid
    non_valid_codes = [
        code for code in languages_codes if code not in avalible_languages.keys()
    ]
    if non_valid_codes:
        raise ValueError(f"Invalid language codes: {non_valid_codes}")

    if negative:
        # take all languages except the ones in the list
        return {k: v for k, v in avalible_languages.items() if k not in languages_codes}
    # take only the languages in the list
    return {k: v for k, v in avalible_languages.items() if k in languages_codes}


@router.get("/create-campaign")
async def create_campaign(
    user_id: int,
    ad_model: Campaign = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["campaign"]

    (
        client,
        campaign_service,
        operation,
        model_dict,
        customer_id,
        operation_create,
        _,
    ) = await _get_necessary_parameters(
        user_id=user_id,
        model=ad_model,
        service_operation_and_function_names=service_operation_and_function_names,
        crud_operation_name="create",
        mandatory_fields=["customer_id"],
        login_customer_id=login_customer_id,
    )
    try:
        # Create a campaign budget resource.
        campaign_budget = _create_campaign_budget(
            client=client,
            customer_id=customer_id,
            amount_micros=ad_model.budget_amount_micros,  # type: ignore
            explicitly_shared=ad_model.budget_explicitly_shared,
        )
        model_dict.pop("budget_amount_micros")
        model_dict.pop("budget_explicitly_shared")
        operation_create.campaign_budget = campaign_budget

        setattr_func = service_operation_and_function_names["setattr_create_func"]
        setattr_func(
            model_dict=model_dict, operation_create=operation_create, client=client
        )

        response = await _mutate(
            campaign_service,
            service_operation_and_function_names["mutate"],
            customer_id,
            operation,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    return f"Created {response.results[0].resource_name}."


@router.get("/update-campaign-language-criterion")
async def update_campaign_language_criterion(
    user_id: int,
    language_criterion_model: CampaignLanguageCriterion = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    client = await _get_client(user_id=user_id, login_customer_id=login_customer_id)
    campaign_service = client.get_service("CampaignService")
    campaign_criterion_service = client.get_service("CampaignCriterionService")
    campaign_criterion_operation = client.get_type("CampaignCriterionOperation")

    campaign_criterion = campaign_criterion_operation.create
    campaign_criterion.campaign = campaign_service.campaign_path(
        customer_id=language_criterion_model.customer_id,
        campaign_id=language_criterion_model.campaign_id,
    )
    try:
        languages = get_languages(
            languages_codes=language_criterion_model.language_codes,
            negative=language_criterion_model.negative,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    # Add one by one the languages to the campaign
    for language_id in languages.values():
        campaign_criterion.language = LanguageInfo(
            language_constant=f"languageConstants/{language_id}"
        )

        await _mutate(
            campaign_criterion_service,
            "mutate_campaign_criteria",
            language_criterion_model.customer_id,
            campaign_criterion_operation,
        )

    return f"Updated campaign '{language_criterion_model.campaign_id}' with language codes: {list(languages.keys())}"


@router.get("/create-ad-group")
async def create_ad_group(
    user_id: int,
    ad_model: AdGroup = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["ad_group"]

    return await _add(
        user_id=user_id,
        model=ad_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "campaign_id"],
        login_customer_id=login_customer_id,
    )


@router.get("/create-ad-group-ad")
async def create_ad_group_ad(
    user_id: int,
    ad_model: AdGroupAd = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["ad"]

    return await _add(
        user_id=user_id,
        model=ad_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_group_id"],
        login_customer_id=login_customer_id,
    )


@router.get("/create-update-ad-copy")
async def create_update_ad_copy(
    user_id: int,
    ad_model: AdCopy = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["ad_copy"]

    return await _update(
        user_id=user_id,
        model=ad_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_id"],
        login_customer_id=login_customer_id,
    )


@router.get("/update-ad-group")
async def update_ad_group(
    user_id: int,
    ad_group_model: AdGroup = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["ad_group"]

    return await _update(
        user_id=user_id,
        model=ad_group_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_group_id"],
        login_customer_id=login_customer_id,
    )


@router.get("/update-campaign")
async def update_campaign(
    user_id: int,
    campaign_model: Campaign = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["campaign"]

    return await _update(
        user_id=user_id,
        model=campaign_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "campaign_id"],
        login_customer_id=login_customer_id,
    )


def _copy_keyword_text_and_match_type(
    model: Criterion, criterion_copy: Dict[str, Any]
) -> None:
    model.keyword_text = (
        model.keyword_text if model.keyword_text else criterion_copy["keyword"]["text"]
    )
    model.keyword_match_type = (
        model.keyword_match_type
        if model.keyword_match_type
        else criterion_copy["keyword"]["matchType"]
    )


REMOVE_EXISTING_AND_CREATE_NEW_CRITERION = "When updating keyword text or match type, a NEW keyword is created and the old one is removed:"


async def _remove_existing_create_new_ad_group_criterion(
    user_id: int,
    ad_group_criterion_model: AdGroupCriterion,
    login_customer_id: Optional[str],
) -> str:
    ad_group_criterion_copy = await _get_existing_ad_group_criterion(
        user_id=user_id,
        customer_id=ad_group_criterion_model.customer_id,
        criterion_id=ad_group_criterion_model.criterion_id,
        login_customer_id=login_customer_id,
    )

    ad_group_criterion_model.status = (
        ad_group_criterion_model.status
        if ad_group_criterion_model.status
        else ad_group_criterion_copy["status"]
    )
    ad_group_criterion_model.negative = (
        ad_group_criterion_model.negative
        if ad_group_criterion_model.negative
        else ad_group_criterion_copy["negative"]
    )

    _copy_keyword_text_and_match_type(
        model=ad_group_criterion_model, criterion_copy=ad_group_criterion_copy
    )

    create_response = await add_keywords_to_ad_group(
        user_id=user_id,
        model=ad_group_criterion_model,
        login_customer_id=login_customer_id,
    )

    remove_resource = RemoveResource(
        customer_id=ad_group_criterion_model.customer_id,
        resource_id=ad_group_criterion_model.criterion_id,
        resource_type="ad_group_criterion",
        parent_id=ad_group_criterion_model.ad_group_id,
    )
    remove_response = await remove_google_ads_resource(
        user_id=user_id,
        model=remove_resource,
        login_customer_id=login_customer_id,
    )

    response = f"{REMOVE_EXISTING_AND_CREATE_NEW_CRITERION}\n{create_response}\n{remove_response}"

    return response


@router.get("/update-ad-group-criterion")
async def update_ad_group_criterion(
    user_id: int,
    ad_group_criterion_model: AdGroupCriterion = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    # keyword text and match type can NOT be updated - NEW ad_group_criterion must be created
    if (
        ad_group_criterion_model.keyword_text
        or ad_group_criterion_model.keyword_match_type
    ):
        return await _remove_existing_create_new_ad_group_criterion(
            user_id=user_id,
            ad_group_criterion_model=ad_group_criterion_model,
            login_customer_id=login_customer_id,
        )

    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT[
        "ad_group_criterion"
    ]

    return await _update(
        user_id=user_id,
        model=ad_group_criterion_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_group_id", "criterion_id"],
        login_customer_id=login_customer_id,
    )


async def _add(
    user_id: int,
    model: AdBase,
    service_operation_and_function_names: Dict[str, Any],
    mandatory_fields: List[str],
    login_customer_id: Optional[str],
) -> str:
    (
        client,
        service,
        operation,
        model_dict,
        customer_id,
        operation_create,
        mandatory_fields_values,
    ) = await _get_necessary_parameters(
        user_id=user_id,
        model=model,
        service_operation_and_function_names=service_operation_and_function_names,
        crud_operation_name="create",
        mandatory_fields=mandatory_fields,
        login_customer_id=login_customer_id,
    )
    try:
        setattr_func = service_operation_and_function_names["setattr_create_func"]
        setattr_func(
            model_dict=model_dict, operation_create=operation_create, client=client
        )

        service_path_function = getattr(
            service, service_operation_and_function_names["service_path_create"]
        )

        # e.g. if service_path is "ad_group_path" root_element will be "ad_group"
        root_element = service_operation_and_function_names[
            "service_path_create"
        ].replace("_path", "")
        setattr(
            operation_create,
            root_element,
            service_path_function(customer_id, *mandatory_fields_values),
        )

        response = await _mutate(
            service,
            service_operation_and_function_names["mutate"],
            customer_id,
            operation,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    return f"Created {response.results[0].resource_name}."


@router.get("/add-negative-keywords-to-campaign")
async def add_negative_keywords_to_campaign(
    user_id: int,
    campaign_criterion_model: CampaignCriterion = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT[
        "campaign_criterion"
    ]

    return await _add(
        user_id=user_id,
        model=campaign_criterion_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "campaign_id"],
        login_customer_id=login_customer_id,
    )


async def _get_existing_campaign_criterion(
    user_id: int,
    customer_id: str,
    criterion_id: Optional[str],
) -> Any:
    query = f"""SELECT campaign_criterion.keyword.match_type, campaign_criterion.keyword.text
FROM campaign_criterion
WHERE campaign_criterion.criterion_id = {criterion_id}"""  # nosec: [B608]
    campaign_criterion = await search(
        user_id=user_id, customer_ids=[customer_id], query=query
    )
    return campaign_criterion[customer_id][0]["campaignCriterion"]


@router.get("/update-campaigns-negative-keywords")
async def update_campaigns_negative_keywords(
    user_id: int, campaign_criterion_model: CampaignCriterion = Depends()
) -> str:
    if (
        campaign_criterion_model.keyword_text is None
        and campaign_criterion_model.keyword_match_type is None
    ):
        return "Only keyword text and match type can be updated for negative keywords."

    campaign_criterion_copy = await _get_existing_campaign_criterion(
        user_id=user_id,
        customer_id=campaign_criterion_model.customer_id,
        criterion_id=campaign_criterion_model.criterion_id,
    )

    _copy_keyword_text_and_match_type(
        model=campaign_criterion_model, criterion_copy=campaign_criterion_copy
    )

    create_response = await add_negative_keywords_to_campaign(
        user_id=user_id,
        campaign_criterion_model=campaign_criterion_model,
    )

    remove_resource = RemoveResource(
        customer_id=campaign_criterion_model.customer_id,
        resource_id=campaign_criterion_model.criterion_id,
        resource_type="campaign_criterion",
        parent_id=campaign_criterion_model.campaign_id,
    )
    remove_response = await remove_google_ads_resource(
        user_id=user_id,
        model=remove_resource,
    )
    response = f"{REMOVE_EXISTING_AND_CREATE_NEW_CRITERION}\n{create_response}\n{remove_response}"

    return response


@router.get("/add-keywords-to-ad-group")
async def add_keywords_to_ad_group(
    user_id: int,
    model: AdGroupCriterion = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT[
        "ad_group_criterion"
    ]

    return await _add(
        user_id=user_id,
        model=model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_group_id"],
        login_customer_id=login_customer_id,
    )


def _get_geo_target_constant_suggestions(
    client: GoogleAdsClient, location_names: List[str], target_type: Optional[str]
) -> Any:
    gtc_service = client.get_service("GeoTargetConstantService")
    gtc_request = client.get_type("SuggestGeoTargetConstantsRequest")

    # The location names to get suggested geo target constants.
    gtc_request.location_names.names.extend(location_names)

    results = gtc_service.suggest_geo_target_constants(gtc_request)

    geo_target_constant_suggestions = results.geo_target_constant_suggestions

    # filter by target type
    if target_type:
        geo_target_constant_suggestions = [
            suggestion
            for suggestion in geo_target_constant_suggestions
            if suggestion.geo_target_constant.target_type == target_type
        ]

    return geo_target_constant_suggestions


def _get_geo_target_constant_by_names(
    client: GoogleAdsClient,
    location_names: List[str],
    target_type: Optional[str],
    add_all_suggestions: Optional[bool],
) -> Union[str | List[str]]:
    geo_target_constant_suggestions = _get_geo_target_constant_suggestions(
        client=client, location_names=location_names, target_type=target_type
    )

    if add_all_suggestions:
        return [
            suggestion.geo_target_constant.id
            for suggestion in geo_target_constant_suggestions
        ]

    return_text = (
        "Below is a list of possible locations in the following format '(name, country_code, target_type)'."
        "Please send them to the client as smart suggestions with type 'manyOf' (do not display the location_id to him):\n\n"
    )
    for suggestion in geo_target_constant_suggestions:
        geo_target_constant = suggestion.geo_target_constant
        text = (
            f"location_id: {geo_target_constant.id}, "
            f"({geo_target_constant.name}, "
            f"{geo_target_constant.country_code}, "
            f"{geo_target_constant.target_type}), "
            f"is found from search term ({suggestion.search_term}).\n"
        )
        return_text += text

    return return_text


def _create_location_op(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str,
    location_id: str,
    negative: Optional[bool],
) -> Any:
    campaign_service = client.get_service("CampaignService")
    geo_target_constant_service = client.get_service("GeoTargetConstantService")

    # Create the campaign criterion.
    campaign_criterion_operation = client.get_type("CampaignCriterionOperation")
    campaign_criterion = campaign_criterion_operation.create
    campaign_criterion.campaign = campaign_service.campaign_path(
        customer_id, campaign_id
    )

    campaign_criterion.location.geo_target_constant = (
        geo_target_constant_service.geo_target_constant_path(location_id)
    )

    campaign_criterion.negative = negative

    return campaign_criterion_operation


def _create_locations_by_ids_to_campaign(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str,
    location_ids: List[str],
    negative: Optional[bool],
) -> str:
    campaign_criterion_service = client.get_service("CampaignCriterionService")

    operations = [
        _create_location_op(
            client, customer_id, campaign_id, location_id, negative=negative
        )
        for location_id in location_ids
    ]

    campaign_criterion_response = campaign_criterion_service.mutate_campaign_criteria(
        customer_id=customer_id, operations=operations
    )

    result_msg = ""
    for result in campaign_criterion_response.results:
        result_msg += f"Added campaign geo target criterion {result.resource_name}.\n"

    return result_msg


@router.get("/create-geo-targeting-for-campaign")
async def create_geo_targeting_for_campaign(
    user_id: int,
    model: GeoTargetCriterion = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    location_names = (
        model.location_names if isinstance(model.location_names, list) else None
    )
    location_ids = model.location_ids if isinstance(model.location_ids, list) else None
    if location_names is None and location_ids is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either location_names or location_ids must be provided.",
        )

    client = await _get_client(user_id=user_id, login_customer_id=login_customer_id)

    if location_ids is None:
        suggestions_or_ids = _get_geo_target_constant_by_names(
            client=client,
            location_names=location_names,  # type: ignore[arg-type]
            target_type=model.target_type,
            add_all_suggestions=model.add_all_suggestions,
        )
        if isinstance(suggestions_or_ids, str):
            return suggestions_or_ids
        else:
            location_ids = suggestions_or_ids
    try:
        return _create_locations_by_ids_to_campaign(
            client=client,
            customer_id=model.customer_id,  # type: ignore
            campaign_id=model.campaign_id,  # type: ignore
            location_ids=location_ids,
            negative=model.negative,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/remove-google-ads-resource")
async def remove_google_ads_resource(
    user_id: int,
    model: RemoveResource = Depends(),
    login_customer_id: Optional[str] = Query(None, title="Login customer ID"),
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT[model.resource_type]

    client = await _get_client(user_id=user_id, login_customer_id=login_customer_id)

    try:
        service = client.get_service(service_operation_and_function_names["service"])
        operation = client.get_type(service_operation_and_function_names["operation"])

        service_path_function = getattr(
            service, service_operation_and_function_names["service_path_update_delete"]
        )

        if model.parent_id is not None:
            resource_name = service_path_function(
                model.customer_id, model.parent_id, model.resource_id
            )
        else:
            resource_name = service_path_function(model.customer_id, model.resource_id)
        operation.remove = resource_name

        response = await _mutate(
            service,
            service_operation_and_function_names["mutate"],
            model.customer_id,
            operation,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

    return f"Removed {response.results[0].resource_name}."


def _link_assets_to_campaign(
    client: Any,
    customer_id: str,
    campaign_id: str,
    resource_names: List[str],
    field_type: Any,
) -> None:
    campaign_service = client.get_service("CampaignService")
    operations = []
    for resource_name in resource_names:
        operation = client.get_type("CampaignAssetOperation")
        campaign_asset = operation.create
        campaign_asset.asset = resource_name
        campaign_asset.campaign = campaign_service.campaign_path(
            customer_id, campaign_id
        )
        campaign_asset.field_type = field_type
        # campaign_asset.field_type = client.enums.AssetFieldTypeEnum.CALLOUT
        operations.append(operation)

    campaign_asset_service = client.get_service("CampaignAssetService")
    campaign_asset_service.mutate_campaign_assets(
        customer_id=customer_id, operations=operations
    )


def _create_sitelink_operations(client: Any, model: NewCampaignSitelinks) -> List[Any]:
    operations = []
    for site_link in model.site_links:
        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.final_urls.extend(site_link.final_urls)
        if site_link.description1:
            asset.sitelink_asset.description1 = site_link.description1
        if site_link.description2:
            asset.sitelink_asset.description2 = site_link.description2
        asset.sitelink_asset.link_text = site_link.link_text
        operations.append(operation)
    return operations


def _create_callout_operations(client: Any, model: CampaignCallouts) -> List[Any]:
    operations = []
    for callout in model.callouts:
        operation = client.get_type("AssetOperation")
        asset = operation.create
        asset.callout_asset.callout_text = callout
        operations.append(operation)
    return operations


def _create_assets(
    client: Any, model: Union[NewCampaignSitelinks, CampaignCallouts]
) -> List[str]:
    if isinstance(model, NewCampaignSitelinks):
        operations = _create_sitelink_operations(client, model)
    else:
        operations = _create_callout_operations(client, model)

    asset_service = client.get_service("AssetService")
    response = asset_service.mutate_assets(
        customer_id=model.customer_id,
        operations=operations,
    )

    resource_names = [result.resource_name for result in response.results]

    return resource_names


def _create_assets_helper(
    client: Any,
    model: Union[NewCampaignSitelinks, CampaignCallouts],
    field_type: Any,
) -> str:
    try:
        resource_names = _create_assets(client, model)
        _link_assets_to_campaign(
            client=client,
            customer_id=model.customer_id,
            campaign_id=model.campaign_id,
            resource_names=resource_names,
            field_type=field_type,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    return (
        f"Linked following assets to campaign '{model.campaign_id}': {resource_names}"
    )


@router.post("/create-sitelinks-for-campaign")
async def create_sitelinks_for_campaign(
    user_id: int,
    model: NewCampaignSitelinks,
) -> str:
    client = await _get_client(
        user_id=user_id, login_customer_id=model.login_customer_id
    )

    result = _create_assets_helper(
        client=client, model=model, field_type=client.enums.AssetFieldTypeEnum.SITELINK
    )

    return result


async def _get_sitelink_resource_names(
    user_id: int,
    model: ExistingCampaignSitelinks,
) -> List[str]:
    sitelink_ids = set(model.sitelink_ids)
    query = f"""
SELECT
  asset.id,
  asset.name
FROM
  asset
WHERE
  asset.type = 'SITELINK'
  AND asset.id IN ({','.join(sitelink_ids)})
"""  # nosec: [B608]

    sitelinks_response = await search(
        user_id=user_id,
        customer_ids=[model.customer_id],
        query=query,
        login_customer_id=model.login_customer_id,
    )

    assets = sitelinks_response[model.customer_id]
    if len(assets) != len(sitelink_ids):
        missing_sitelinks = sitelink_ids - {asset["asset"]["id"] for asset in assets}
        raise ValueError(f"Sitelinks with IDs {missing_sitelinks} not found.")

    return [asset["asset"]["resourceName"] for asset in assets]


@router.post("/add-sitelinks-to-campaign")
async def add_sitelinks_to_campaign(
    user_id: int,
    model: ExistingCampaignSitelinks,
) -> str:
    try:
        client = await _get_client(
            user_id=user_id, login_customer_id=model.login_customer_id
        )
        resource_names = await _get_sitelink_resource_names(user_id, model)
        if len(resource_names) == 0:
            return "No sitelinks found to add to the campaign."
        _link_assets_to_campaign(
            client=client,
            customer_id=model.customer_id,
            campaign_id=model.campaign_id,
            resource_names=resource_names,
            field_type=client.enums.AssetFieldTypeEnum.SITELINK,
        )
        return f"Linked following sitelinks to campaign '{model.campaign_id}': {resource_names}"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/create-callouts-for-campaign")
async def create_callouts_for_campaign(
    user_id: int,
    model: CampaignCallouts,
) -> str:
    client = await _get_client(
        user_id=user_id, login_customer_id=model.login_customer_id
    )

    result = _create_assets_helper(
        client=client, model=model, field_type=client.enums.AssetFieldTypeEnum.CALLOUT
    )

    return result


async def _get_callout_resource_names(
    user_id: int,
    model: CampaignCallouts,
) -> List[str]:
    query = f"""
SELECT
  asset.id,
  asset.name,
  asset.type,
  asset.callout_asset.callout_text
FROM
  asset
WHERE
  asset.type = 'CALLOUT' AND
  asset.callout_asset.callout_text IN ({", ".join([f'"{text}"' for text in model.callouts])})"""  # nosec: [B608]
    callouts_response = await search(
        user_id=user_id,
        customer_ids=[model.customer_id],
        query=query,
        login_customer_id=model.login_customer_id,
    )

    callout_texts_added = []
    resource_names = []
    for asset in callouts_response[model.customer_id]:
        # don't add duplicates
        if asset["asset"]["calloutAsset"]["calloutText"] not in callout_texts_added:
            resource_names.append(asset["asset"]["resourceName"])
            callout_texts_added.append(asset["asset"]["calloutAsset"]["calloutText"])

    if len(callout_texts_added) != len(model.callouts):
        missing_callouts = set(model.callouts) - set(callout_texts_added)
        raise ValueError(f"Callouts not found: {missing_callouts}")

    return resource_names


@router.post("/add-callouts-to-campaign")
async def add_callouts_to_campaign(
    user_id: int,
    model: CampaignCallouts,
) -> str:
    try:
        callout_resource_names = await _get_callout_resource_names(user_id, model)
        if len(callout_resource_names) == 0:
            return "No callouts found to add to the campaign."
        client = await _get_client(
            user_id=user_id, login_customer_id=model.login_customer_id
        )
        _link_assets_to_campaign(
            client=client,
            customer_id=model.customer_id,
            campaign_id=model.campaign_id,
            resource_names=callout_resource_names,
            field_type=client.enums.AssetFieldTypeEnum.CALLOUT,
        )
        return f"Linked following callouts to campaign '{model.campaign_id}': {callout_resource_names}"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


async def _get_shared_set_resource_name(
    user_id: int,
    model: CampaignSharedSet,
) -> str:
    query = f"""
SELECT
    shared_set.id,
    shared_set.name
FROM
    shared_set
WHERE
    shared_set.name = "{model.shared_set_name}" AND
    shared_set.type = "NEGATIVE_KEYWORDS" AND
    shared_set.status != "REMOVED"
"""  # nosec: [B608]
    shared_set_response = await search(
        user_id=user_id,
        customer_ids=[model.customer_id],
        query=query,
        login_customer_id=model.login_customer_id,
    )

    if not shared_set_response[model.customer_id]:
        raise ValueError(
            f"Negative keywords shared set '{model.shared_set_name}' not found."
        )

    return shared_set_response[model.customer_id][0]["sharedSet"]["resourceName"]  # type: ignore[no-any-return]


@router.post("/add-shared-set-to-campaign")
async def add_shared_set_to_campaign(
    user_id: int,
    model: CampaignSharedSet,
) -> str:
    try:
        shared_set_resource_name = await _get_shared_set_resource_name(
            user_id=user_id, model=model
        )

        client = await _get_client(
            user_id=user_id, login_customer_id=model.login_customer_id
        )
        campaign_service = client.get_service("CampaignService")
        campaign_shared_set_service = client.get_service("CampaignSharedSetService")
        campaign_set_operation = client.get_type("CampaignSharedSetOperation")
        campaign_set = campaign_set_operation.create
        campaign_set.campaign = campaign_service.campaign_path(
            model.customer_id, model.campaign_id
        )
        campaign_set.shared_set = shared_set_resource_name

        campaign_shared_set_resource_name = (
            campaign_shared_set_service.mutate_campaign_shared_sets(
                customer_id=model.customer_id, operations=[campaign_set_operation]
            )
        )

        return f"Linked campaign shared set {campaign_shared_set_resource_name.results[0].resource_name}."

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


def _add_assets_to_asset_set(
    client: Any,
    customer_id: str,
    asset_resource_names: List[str],
    asset_set_resource_name: str,
) -> str:
    """Adds assets to an asset set by creating an asset set asset link.

    Args:
        client: an initialized GoogleAdsClient instance.
        customer_id: a client customer ID.
        asset_resource_names: a list of asset resource names.
        asset_set_resource_name: a resource name for an asset set.
    """
    operations = []
    for resource_name in asset_resource_names:
        # Creates an asset set asset operation and adds it to the list of
        # operations.
        operation = client.get_type("AssetSetAssetOperation")
        asset_set_asset = operation.create
        asset_set_asset.asset = resource_name
        asset_set_asset.asset_set = asset_set_resource_name
        operations.append(operation)

    # Issues a mutate request to add the asset set assets and prints its
    # information.
    asset_set_asset_service = client.get_service("AssetSetAssetService")
    response = asset_set_asset_service.mutate_asset_set_assets(
        customer_id=customer_id, operations=operations
    )

    return_text = ""
    for result in response.results:
        return_text += f"Created an asset set asset link with resource name '{result.resource_name}'\n"
    return return_text


@router.post("/add-items-to-page-feed")
async def add_items_to_page_feed(
    user_id: int,
    model: AddPageFeedItems,
) -> str:
    client = await _get_client(
        user_id=user_id, login_customer_id=model.login_customer_id
    )
    operations = []

    # Creates one asset per URL.
    for url, label in model.urls_and_labels.items():
        # Creates an asset operation and adds it to the list of operations.
        operation = client.get_type("AssetOperation")
        asset = operation.create
        page_feed_asset = asset.page_feed_asset
        page_feed_asset.page_url = url
        # Recommended: adds labels to the asset. These labels can be used later
        # in ad group targeting to restrict the set of pages that can serve.
        if label:
            page_feed_asset.labels.append(label)
        operations.append(operation)

    # Issues a mutate request to add the assets and prints its information.
    asset_service = client.get_service("AssetService")
    response = asset_service.mutate_assets(
        customer_id=model.customer_id, operations=operations
    )

    resource_names = []
    return_text = ""
    for result in response.results:
        resource_name = result.resource_name
        return_text += f"Created an asset with resource name: '{resource_name}'\n"
        resource_names.append(resource_name)

    return _add_assets_to_asset_set(
        client=client,
        customer_id=model.customer_id,
        asset_resource_names=resource_names,
        asset_set_resource_name=model.asset_set_resource_name,
    )
