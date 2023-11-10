import json
import urllib.parse
from contextlib import asynccontextmanager
from os import environ
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import json_format
from prisma import Prisma

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
async def get_db_connection(db_url: Optional[str] = None):
    if not db_url:
        db_url = environ.get("DATABASE_URL")
    db = Prisma(datasource={"url": db_url})
    await db.connect()
    try:
        yield db
    finally:
        await db.disconnect()


async def get_user(user_id: int):
    curr_db_url = environ.get("DATABASE_URL")
    wasp_db_url = curr_db_url.replace(curr_db_url.split("/")[-1], "waspdb")
    async with get_db_connection(db_url=wasp_db_url) as db:
        user = await db.query_first(f'SELECT * from "User" where id={user_id}')
    if not user:
        raise HTTPException(status_code=404, detail="user_id not found")
    return user


# Route 1: Redirect to Google OAuth
@router.get("/login")
async def get_login_url(request: Request, user_id: int = Query(title="User ID")):
    user = await get_user(user_id=user_id)

    google_oauth_url = (
        f"{oauth2_settings['auth_uri']}?client_id={oauth2_settings['clientId']}"
        f"&redirect_uri={oauth2_settings['redirectUri']}&response_type=code"
        f"&scope={urllib.parse.quote_plus('https://www.googleapis.com/auth/adwords email')}"
        f"&access_type=offline&prompt=consent&state={user_id}"
    )
    return {"login_url": google_oauth_url}


# Route 2: Save user credentials/token to a JSON file
@router.get("/login/callback")
async def login_callback(
    code: str = Query(title="Authorization Code"), state: str = Query(title="State")
):
    user_id = state
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
        row = await db.gauth.upsert(
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

    return {"message": "User credentials saved successfully"}


async def load_user_credentials(user_id):
    user = await get_user(user_id=user_id)
    async with get_db_connection() as db:
        data = await db.gauth.find_unique_or_raise(where={"user_id": user_id})

    return data.creds


# Initialize Google Ads API client
def create_google_ads_client(user_credentials):
    # Create a dictionary with the required structure for GoogleAdsClient
    google_ads_credentials = {
        "developer_token": environ.get("DEVELOPER_TOKEN"),
        "use_proto_plus": False,
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
async def list_accessible_customers(user_id: int = Query(title="User ID")):
    user_credentials = await load_user_credentials(user_id)
    client = create_google_ads_client(user_credentials)
    customer_service = client.get_service("CustomerService")
    accessible_customers = customer_service.list_accessible_customers()

    customer_ids = [x.split("/")[-1] for x in accessible_customers.resource_names]
    return customer_ids


# Route 4: Fetch user's ad campaign data
@router.get("/search")
async def search(
    user_id: int = Query(title="User ID"),
    customer_ids: List[str] = Query(None),
    query: str = Query(None, title="Google ads query"),
):
    user_credentials = await load_user_credentials(user_id)
    client = create_google_ads_client(user_credentials)
    service = client.get_service("GoogleAdsService")

    # Replace this with your actual Google Ads API query to fetch campaign data
    if not query:
        query = (
            f"SELECT campaign.id, campaign.name, ad_group.id, ad_group.name "
            "FROM keyword_view WHERE segments.date DURING LAST_7_DAYS"
        )
    print(f"{query=}")

    if not customer_ids:
        customer_ids = await list_accessible_customers(user_id=user_id)
    print(f"{customer_ids=}")

    campaign_data = {}

    for customer_id in customer_ids:
        try:
            response = service.search(customer_id=customer_id, query=query)
            l = []
            for row in response:
                json_str = json_format.MessageToJson(row)
                l.append(json.loads(json_str))
            campaign_data[customer_id] = l
        except GoogleAdsException as e:
            print(f"Exception for {customer_id}")

    return campaign_data
