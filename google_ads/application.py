import json
import urllib.parse
from os import environ
from typing import Any, Dict, List, Tuple, Union

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
    AdGroup,
    AdGroupAd,
    AdGroupCriterion,
    Campaign,
    CampaignCriterion,
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


def _set_fields(
    client: GoogleAdsClient,
    model_dict: Dict[str, Any],
    operation: Any,
    operation_update: Any,
) -> None:
    for attribute_name, attribute_value in model_dict.items():
        if attribute_value:
            setattr(operation_update, attribute_name, attribute_value)

    # Retrieve a FieldMask for the fields configured in the campaign/ad_group/ad_group_ad.
    client.copy_from(
        operation.update_mask,
        protobuf_helpers.field_mask(None, operation_update._pb),  # type: ignore[no-untyped-call]
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
            service, service_operation_and_function_names["service_path"]
        )
        operation_update.resource_name = service_path_function(
            customer_id, *mandatory_fields_values
        )

        _set_fields(
            client=client,
            model_dict=model_dict,
            operation=operation,
            operation_update=operation_update,
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


def _keywords_setattr(model_dict: Dict[str, Any], operation_create: Any) -> None:
    for attribute_name, attribute_value in model_dict.items():
        if attribute_value:
            if "keyword_" in attribute_name:
                attribute_name = attribute_name.replace("keyword_", "")
                setattr(operation_create.keyword, attribute_name, attribute_value)
            else:
                setattr(operation_create, attribute_name, attribute_value)


GOOGLE_ADS_RESOURCE_DICT: Dict[str, Dict[str, Any]] = {
    "campaign": {
        "service": "CampaignService",
        "operation": "CampaignOperation",
        "mutate": "mutate_campaigns",
        "service_path": "campaign_path",
    },
    "ad_group": {
        "service": "AdGroupService",
        "operation": "AdGroupOperation",
        "mutate": "mutate_ad_groups",
        "service_path": "ad_group_path",
    },
    "ad": {
        "service": "AdGroupAdService",
        "operation": "AdGroupAdOperation",
        "mutate": "mutate_ad_group_ads",
        "service_path": "ad_group_ad_path",
    },
    "ad_group_criterion": {
        "service": "AdGroupCriterionService",
        "operation": "AdGroupCriterionOperation",
        "mutate": "mutate_ad_group_criteria",
        "service_path": "ad_group_path",
        "setattr_func": _keywords_setattr,
    },
    "campaign_criterion": {
        "service": "CampaignCriterionService",
        "operation": "CampaignCriterionOperation",
        "mutate": "mutate_campaign_criteria",
        "service_path": "campaign_path",
        "setattr_func": _keywords_setattr,
    },
}


@router.get("/update-ad")
async def update_ad(user_id: int, ad_model: AdGroupAd = Depends()) -> str:
    global GOOGLE_ADS_RESOURCE_DICT
    service_operation_and_function_names = GOOGLE_ADS_RESOURCE_DICT["ad"]

    return await _update(
        user_id=user_id,
        model=ad_model,
        service_operation_and_function_names=service_operation_and_function_names,
        mandatory_fields=["customer_id", "ad_group_id", "ad_id"],
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


@router.get("/update-ad-group-criterion")
async def update_ad_group_criterion(
    user_id: int, ad_group_criterion_model: AdGroupCriterion = Depends()
) -> str:
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
        _,
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
        setattr_func(model_dict=model_dict, operation_create=operation_create)

        service_path_function = getattr(
            service, service_operation_and_function_names["service_path"]
        )

        # e.g. if service_path is "ad_group_path" root_element will be "ad_group"
        root_element = service_operation_and_function_names["service_path"].replace(
            "_path", ""
        )
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
