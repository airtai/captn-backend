import json
import urllib.parse
from contextlib import asynccontextmanager
from os import environ
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.api_core import protobuf_helpers
from google.protobuf import json_format
from prisma import Prisma  # type: ignore[attr-defined]

from .model import AdBase, AdGroup, AdGroupAd, Campaign

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


@asynccontextmanager
async def get_db_connection(db_url: Optional[str] = None) -> Prisma:
    if not db_url:
        db_url = environ.get("DATABASE_URL")
    db = Prisma(datasource={"url": db_url})
    await db.connect()
    try:
        yield db
    finally:
        await db.disconnect()


async def get_wasp_db_url() -> str:
    curr_db_url = environ.get("DATABASE_URL")
    wasp_db_url = curr_db_url.replace(curr_db_url.split("/")[-1], "waspdb")  # type: ignore[union-attr]
    return wasp_db_url


async def get_user(user_id: Union[int, str]) -> Any:
    wasp_db_url = await get_wasp_db_url()
    async with get_db_connection(db_url=wasp_db_url) as db:
        user = await db.query_first(
            f'SELECT * from "User" where id={user_id}'  # nosec: [B608]
        )
    if not user:
        raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")
    return user


async def get_user_id_chat_id_from_conversation(
    conv_id: Union[int, str]
) -> Tuple[Any, Any]:
    wasp_db_url = await get_wasp_db_url()
    async with get_db_connection(db_url=wasp_db_url) as db:
        conversation = await db.query_first(
            f'SELECT * from "Conversation" where id={conv_id}'  # nosec: [B608]
        )
        if not conversation:
            raise HTTPException(status_code=404, detail=f"conv_id {conv_id} not found")
    user_id = conversation["userId"]
    chat_id = conversation["chatId"]
    return user_id, chat_id


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
) -> Dict[str, str]:
    is_authenticated = await is_authenticated_for_ads(user_id=user_id)
    if is_authenticated:
        return {"login_url": "User is already authenticated"}

    google_oauth_url = (
        f"{oauth2_settings['auth_uri']}?client_id={oauth2_settings['clientId']}"
        f"&redirect_uri={oauth2_settings['redirectUri']}&response_type=code"
        f"&scope={urllib.parse.quote_plus('https://www.googleapis.com/auth/adwords email')}"
        f"&access_type=offline&prompt=consent&state={conv_id}"
    )
    markdown_url = f"[Click Here]({google_oauth_url})"
    return {"login_url": markdown_url}


# Route 2: Save user credentials/token to a JSON file
@router.get("/login/callback")
async def login_callback(
    code: str = Query(title="Authorization Code"), state: str = Query(title="State")
) -> RedirectResponse:
    conv_id = state
    user_id, chat_id = await get_user_id_chat_id_from_conversation(conv_id)
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

    redirect_domain = environ.get("REDIRECT_DOMAIN", "https://captn.ai")
    logged_in_message = "I have successfully logged in"
    redirect_uri = f"{redirect_domain}/chat/{chat_id}?msg={logged_in_message}"
    return RedirectResponse(redirect_uri)


async def load_user_credentials(user_id: Union[int, str]) -> Any:
    await get_user(user_id=user_id)
    async with get_db_connection() as db:
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
        accessible_customers = customer_service.list_accessible_customers()

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
            try:
                response = service.search(customer_id=customer_id, query=query)
                l = []  # noqa
                for row in response:
                    json_str = json_format.MessageToJson(row)
                    l.append(json.loads(json_str))
                campaign_data[customer_id] = l
            except GoogleAdsException:
                print(f"Exception for {customer_id}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

    return campaign_data


AVALIABLE_KEYS = ["campaign", "ad_group", "ad_group_ad"]

async def _update(
    user_id: int, model: AdBase, key_service_operation: Dict[str, str]
) -> str:
    user_credentials = await load_user_credentials(user_id)
    client = create_google_ads_client(
        user_credentials=user_credentials, use_proto_plus=True
    )

    model_dict = model.model_dump()
    customer_id = model_dict.pop("customer_id")

    key = key_service_operation["key"]
    if key not in AVALIABLE_KEYS:
        raise KeyError(f"key: {key} is not supported")

    if key == "campaign":
        status_enum = client.enums.CampaignStatusEnum
    else:
        status_enum = client.enums.AdGroupStatusEnum

    if model_dict["status"] == "ENABLED":
        model_dict["status"] = status_enum.ENABLED
    elif model_dict["status"] == "PAUSED":
        model_dict["status"] = status_enum.PAUSED

    service = client.get_service(key_service_operation["service"])
    operation = client.get_type(key_service_operation["operation"])
    
    try:
        operation_update = operation.update

        if key == "ad_group_ad":
            ad_group_id = model_dict.pop("ad_group_id")
            ad_id = model_dict.pop("ad_id")
            operation_update.resource_name = service.ad_group_ad_path(
                customer_id, ad_group_id, ad_id
            )
        elif key == "ad_group":
            ad_group_id = model_dict.pop("ad_group_id")
            operation_update.resource_name = service.ad_group_path(
                customer_id, ad_group_id
            )
        else:
            campaign_id = model_dict.pop("campaign_id")
            operation_update.resource_name = service.campaign_path(
                customer_id, campaign_id
            )

        for attribute_name, attribute_value in model_dict.items():
            if attribute_value:
                setattr(operation_update, attribute_name, attribute_value)

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask(None, operation_update._pb),  # type: ignore[no-untyped-call]
        )

        if key == "ad_group_ad":
            response = service.mutate_ad_group_ads(
                customer_id=customer_id, operations=[operation]
            )
        elif key == "ad_group":
            response = service.mutate_ad_groups(
                customer_id=customer_id, operations=[operation]
            )
        else:
            response = service.mutate_campaigns(
                customer_id=customer_id, operations=[operation]
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    return f"Updated {response.results[0].resource_name}."


@router.get("/update-ad")
async def update_ad(user_id: int, ad_model: AdGroupAd = Depends()) -> str:
    key_service_operation = {
        "key": "ad_group_ad",
        "service": "AdGroupAdService",
        "operation": "AdGroupAdOperation",
    }

    return await _update(
        user_id=user_id, model=ad_model, key_service_operation=key_service_operation
    )


@router.get("/update-ad-group")
async def update_ad_group(user_id: int, ad_group_model: AdGroup = Depends()) -> str:
    key_service_operation = {
        "key": "ad_group",
        "service": "AdGroupService",
        "operation": "AdGroupOperation",
    }

    return await _update(
        user_id=user_id,
        model=ad_group_model,
        key_service_operation=key_service_operation,
    )


@router.get("/update-campaign")
async def update_campaign(user_id: int, campaign_model: Campaign = Depends()) -> str:
    key_service_operation = {
        "key": "campaign",
        "service": "CampaignService",
        "operation": "CampaignOperation",
    }

    return await _update(
        user_id=user_id,
        model=campaign_model,
        key_service_operation=key_service_operation,
    )