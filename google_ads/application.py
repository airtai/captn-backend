import json
import urllib.parse
from os import environ
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from asyncer import asyncify
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from google.ads.googleads.client import GoogleAdsClient
from google.api_core import protobuf_helpers
from google.protobuf import json_format

from captn.captn_agents.helpers import get_db_connection, get_wasp_db_url

from .model import (
    AdBase,
    AdCopy,
    AdGroup,
    AdGroupAd,
    AdGroupCriterion,
    Campaign,
    CampaignCriterion,
    Criterion,
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


async def get_user(user_id: Union[int, str]) -> Any:
    wasp_db_url = await get_wasp_db_url()
    async with get_db_connection(db_url=wasp_db_url) as db:  # type: ignore[var-annotated]
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


async def get_user_id_from_chat(chat_id: Union[int, str]) -> Any:
    wasp_db_url = await get_wasp_db_url()
    async with get_db_connection(db_url=wasp_db_url) as db:  # type: ignore[var-annotated]
        chat = await db.query_first(
            f'SELECT * from "Chat" where id={chat_id}'  # nosec: [B608]
        )
        if not chat:
            raise HTTPException(status_code=404, detail=f"chat {chat} not found")
    user_id = chat["userId"]
    return user_id


async def is_authenticated_for_ads(user_id: int) -> bool:
    await get_user(user_id=user_id)
    async with get_db_connection() as db:  # type: ignore[var-annotated]
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
    # chat_id: int = Query(title="Chat ID"),
) -> Dict[str, str]:
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
    user_id = await get_user_id_from_chat(chat_id)
    # user_id, chat_id = await get_user_id_chat_id_from_conversation(conv_id)
    user = await get_user(user_id=user_id)

    token_request_data = {
        "code": code,
        "client_id": oauth2_settings["clientId"],
        "client_secret": oauth2_settings["clientSecret"],
        "redirect_uri": oauth2_settings["redirectUri"],
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            oauth2_settings["tokenUrl"], data=token_request_data
        )

    if response.status_code == 200:
        token_data = response.json()

    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )

    if userinfo_response.status_code == 200:
        user_info = userinfo_response.json()
    async with get_db_connection() as db:  # type: ignore[var-annotated]
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
    redirect_uri = f"{redirect_domain}/chat/{chat_id}?msg={logged_in_message}"
    return RedirectResponse(redirect_uri)


async def load_user_credentials(user_id: Union[int, str]) -> Any:
    await get_user(user_id=user_id)
    async with get_db_connection() as db:  # type: ignore[var-annotated]
        data = await db.gauth.find_unique_or_raise(where={"user_id": user_id})

    return data.creds


# Initialize Google Ads API client
def create_google_ads_client(
    user_credentials: Dict[str, Any], use_proto_plus: bool = False
) -> GoogleAdsClient:
    # Create a dictionary with the required structure for GoogleAdsClient
    google_ads_credentials = {
        "developer_token": environ.get("DEVELOPER_TOKEN"),
        "use_proto_plus": use_proto_plus,
        "client_id": oauth2_settings["clientId"],
        "client_secret": oauth2_settings["clientSecret"],
        "refresh_token": user_credentials["refresh_token"],
        # "login_customer_id": "7119828439",
    }

    # Initialize the Google Ads API client with the properly structured dictionary
    client = GoogleAdsClient.load_from_dict(google_ads_credentials)
    return client


# Route 3: List accessible customer ids
@router.get("/list-accessible-customers")
async def list_accessible_customers(user_id: int = Query(title="User ID")) -> List[str]:
    try:
        user_credentials = await load_user_credentials(user_id)
        client = create_google_ads_client(user_credentials)
        customer_service = client.get_service("CustomerService")
        accessible_customers = await asyncify(
            customer_service.list_accessible_customers
        )()

        customer_ids = [x.split("/")[-1] for x in accessible_customers.resource_names]
        return customer_ids
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
) -> Dict[str, List[Any]]:
    user_credentials = await load_user_credentials(user_id)
    client = create_google_ads_client(user_credentials)
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


AVALIABLE_KEYS = ["campaign", "ad_group", "ad_group_ad", "ad_group_criterion"]


async def _get_client(user_id: int) -> GoogleAdsClient:
    user_credentials = await load_user_credentials(user_id)
    client = create_google_ads_client(
        user_credentials=user_credentials, use_proto_plus=True
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
        if attribute_value:
            setattr(operation_update, attribute_name, attribute_value)

    _retrieve_field_mask(
        client=client, operation=operation, operation_update=operation_update
    )


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
        headline_or_description = client.get_type("AdTextAsset")
        headline_or_description.text = new_text
        updated_fields.append(headline_or_description)

    getattr(operation_update.responsive_search_ad, update_field).extend(updated_fields)


async def _set_fields_ad_copy(
    client: GoogleAdsClient,
    model_or_dict: AdCopy,
    operation: Any,
    operation_update: Any,
    user_id: int,
) -> None:
    # for attribute_name, attribute_value in model_dict.items():
    #     if attribute_value:
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

        if modify_headlines:
            update_field = "headlines"
            new_text = model_or_dict.headline
            _set_headline_or_description(
                client=client,
                operation_update=operation_update,
                update_field=update_field,
                new_text=new_text,
                update_existing_index=model_or_dict.update_existing_headline_index,
                responsive_search_ad=responsive_search_ad,
            )

        if modify_descriptions:
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

    if model_or_dict.final_url:
        final_url = model_or_dict.final_url
        final_url = final_url if final_url.startswith("http") else f"http://{final_url}"
        operation_update.final_urls.append(final_url)
    if model_or_dict.final_mobile_urls:
        operation_update.final_mobile_urls.append(model_or_dict.final_mobile_urls)

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
) -> Tuple[GoogleAdsClient, Any, Any, Dict[str, Any], str, Any, List[Any]]:
    client = await _get_client(user_id=user_id)

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
    criterion_id: str,
) -> Any:
    query = f"""SELECT ad_group_criterion.status, ad_group_criterion.negative,
ad_group_criterion.keyword.match_type, ad_group_criterion.keyword.text
FROM ad_group_criterion
WHERE ad_group_criterion.criterion_id = {criterion_id}"""  # nosec: [B608]
    ad_group_criterion = await search(
        user_id=user_id, customer_ids=[customer_id], query=query
    )
    return ad_group_criterion[customer_id][0]["adGroupCriterion"]


async def _update(
    user_id: int,
    model: AdBase,
    service_operation_and_function_names: Dict[str, Any],
    mandatory_fields: List[str],
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
    )

    try:
        service_path_function = getattr(
            service, service_operation_and_function_names["service_path_update_delete"]
        )
        operation_update.resource_name = service_path_function(
            customer_id, *mandatory_fields_values
        )

        model_or_dict = model if isinstance(model, AdCopy) else model_dict
        await service_operation_and_function_names["set_fields"](
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


def _keywords_setattr(
    model_dict: Dict[str, Any], operation_create: Any, client: Any
) -> None:
    for attribute_name, attribute_value in model_dict.items():
        if attribute_value:
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
        else f"http://{model_dict['final_url']}"
    )
    operation_create.ad.final_urls.append(final_url)

    # Set a pinning to always choose this asset for HEADLINE_1. Pinning is
    # optional; if no pinning is set, then headlines and descriptions will be
    # rotated and the ones that perform best will be used more often.

    # Headline 1
    served_asset_enum = client.enums.ServedAssetFieldTypeEnum.HEADLINE_1
    pinned_headline = _create_ad_text_asset(
        client, model_dict["headlines"][0], served_asset_enum
    )

    # Headlines 2-15
    headlines = [pinned_headline]
    headlines += [
        _create_ad_text_asset(client, headline)
        for headline in model_dict["headlines"][1:]
    ]
    operation_create.ad.responsive_search_ad.headlines.extend(headlines)

    descriptions = [
        _create_ad_text_asset(client, desc) for desc in model_dict["descriptions"]
    ]

    operation_create.ad.responsive_search_ad.descriptions.extend(descriptions)

    # TODO:
    # Paths
    # First and second part of text that can be appended to the URL in the ad.
    # If you use the examples below, the ad will show
    # https://www.example.com/all-inclusive/deals
    # operation_create.ad.responsive_search_ad.path1 = "all-inclusive"
    # operation_create.ad.responsive_search_ad.path2 = "deals"


GOOGLE_ADS_RESOURCE_DICT: Dict[str, Dict[str, Any]] = {
    "campaign": {
        "service": "CampaignService",
        "operation": "CampaignOperation",
        "mutate": "mutate_campaigns",
        "service_path_create": None,  # TODO
        "service_path_update_delete": "campaign_path",
        "set_fields": _set_fields,
    },
    "ad_group": {
        "service": "AdGroupService",
        "operation": "AdGroupOperation",
        "mutate": "mutate_ad_groups",
        "service_path_create": "campaign_path",
        "service_path_update_delete": "ad_group_path",
        "set_fields": _set_fields,
    },
    "ad": {
        "service": "AdGroupAdService",
        "operation": "AdGroupAdOperation",
        "mutate": "mutate_ad_group_ads",
        "service_path_create": "ad_group_path",
        "service_path_update_delete": "ad_group_ad_path",
        "setattr_func": _create_ad_group_ad_set_attr,
        "set_fields": _set_fields,
    },
    "ad_copy": {
        "service": "AdService",
        "operation": "AdOperation",
        "mutate": "mutate_ads",
        "service_path_update_delete": "ad_path",
        "set_fields": _set_fields_ad_copy,
    },
    "ad_group_criterion": {
        "service": "AdGroupCriterionService",
        "operation": "AdGroupCriterionOperation",
        "mutate": "mutate_ad_group_criteria",
        "service_path_create": "ad_group_path",
        "service_path_update_delete": "ad_group_criterion_path",
        "setattr_func": _keywords_setattr,
        "set_fields": _set_fields,
    },
    "campaign_criterion": {
        "service": "CampaignCriterionService",
        "operation": "CampaignCriterionOperation",
        "mutate": "mutate_campaign_criteria",
        "service_path_create": "campaign_path",
        "service_path_update_delete": "campaign_criterion_path",
        "setattr_func": _keywords_setattr,
        "set_fields": _set_fields,
    },
}


@router.get("/update-ad-group-ad")
async def update_ad_group_ad(user_id: int, ad_model: AdGroupAd = Depends()) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["ad"]

    return await _update(
        user_id=user_id,
        model=ad_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_group_id", "ad_id"],
    )


@router.get("/create-ad-group-ad")
async def create_ad_group_ad(user_id: int, ad_model: AdGroupAd = Depends()) -> str:
    print(ad_model)
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["ad"]

    return await _add(
        user_id=user_id,
        model=ad_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_group_id"],
    )


@router.get("/create-update-ad-copy")
async def create_update_ad_copy(user_id: int, ad_model: AdCopy = Depends()) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["ad_copy"]

    return await _update(
        user_id=user_id,
        model=ad_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_id"],
    )


@router.get("/update-ad-group")
async def update_ad_group(user_id: int, ad_group_model: AdGroup = Depends()) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["ad_group"]

    return await _update(
        user_id=user_id,
        model=ad_group_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_group_id"],
    )


@router.get("/update-campaign")
async def update_campaign(user_id: int, campaign_model: Campaign = Depends()) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["campaign"]

    return await _update(
        user_id=user_id,
        model=campaign_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "campaign_id"],
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
    user_id: int, ad_group_criterion_model: AdGroupCriterion
) -> str:
    ad_group_criterion_copy = await _get_existing_ad_group_criterion(
        user_id=user_id,
        customer_id=ad_group_criterion_model.customer_id,
        criterion_id=ad_group_criterion_model.criterion_id,
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
    )

    response = f"{REMOVE_EXISTING_AND_CREATE_NEW_CRITERION}\n{create_response}\n{remove_response}"

    return response


@router.get("/update-ad-group-criterion")
async def update_ad_group_criterion(
    user_id: int, ad_group_criterion_model: AdGroupCriterion = Depends()
) -> str:
    # keyword text and match type can NOT be updated - NEW ad_group_criterion must be created
    if (
        ad_group_criterion_model.keyword_text
        or ad_group_criterion_model.keyword_match_type
    ):
        return await _remove_existing_create_new_ad_group_criterion(
            user_id=user_id,
            ad_group_criterion_model=ad_group_criterion_model,
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
    )


async def _add(
    user_id: int,
    model: AdBase,
    service_operation_and_function_names: Dict[str, Any],
    mandatory_fields: List[str],
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
    )
    try:
        setattr_func = service_operation_and_function_names["setattr_func"]
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
    user_id: int, campaign_criterion_model: CampaignCriterion = Depends()
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
    )


async def _get_existing_campaign_criterion(
    user_id: int,
    customer_id: str,
    criterion_id: str,
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
    user_id: int, model: AdGroupCriterion = Depends()
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
    )


@router.get("/remove-google-ads-resource")
async def remove_google_ads_resource(
    user_id: int, model: RemoveResource = Depends()
) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT[model.resource_type]

    client = await _get_client(user_id=user_id)

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
