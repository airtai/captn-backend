import json
from contextlib import asynccontextmanager
from typing import List, Optional, Dict

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import json_format
from prisma import Prisma
from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from os import environ

app = FastAPI()

# Load client secret data from the JSON file
with open("client_secret.json") as secret_file:
    client_secret_data = json.load(secret_file)

# OAuth2 configuration
oauth2_settings = {
    "auth_uri": client_secret_data["web"]["auth_uri"],
    "tokenUrl": client_secret_data["web"]["token_uri"],
    "clientId": client_secret_data["web"]["client_id"],
    "clientSecret": client_secret_data["web"]["client_secret"],
    "redirectUri": "http://localhost:9000/login/callback",
}

# Setting up Azure OpenAI instance
azure_openai_client = AsyncAzureOpenAI(
    api_key=client_secret_data["azure_openai"]["api_key"],
    api_version=client_secret_data["azure_openai"]["api_version"],
    azure_endpoint=client_secret_data["azure_openai"]["azure_endpoint"],
    max_retries=5, # default is 2
)

SYSTEM_PROMPT = """
You are Captn AI, a digital marketing assistant for small businesses. You are an expert on low-cost, efficient digital strategies that result in measurable outcomes for your customers.

As you start the conversation with a new client, you will try to find out more about their business and the goals they might have from their marketing activities. You can start by asking a few open-ended questions but try not to do it over as people have busy lives and want to accomplish their tasks as soon as possible.

You can write and execute Python code. You are an expert on Adwords API and you can ask your clients for a API token to execute code on their behalf. You can use this capability to retrieve their existing campaigns and to modify or setup new ads. Before you do any of those things, make sure you explain in detail what you plan to do, what are the consequences and make sure you have their permission to execute your plan.

GUIDELINES:
Be concise and to the point. Avoid long sentences. When asking questions, prefer questions with simple yes/no answers.

You are Captn and your language should reflect that. Use sailing metaphors whenever possible, but don't over do it.

Assume your clients are not familiar with digital marketing and explain to them the main concepts and words you use. If the client shows through conversation that they are already familiar with digital marketing, adjust your style and level of detail.

Do not assume that the client has any digital presence, or at least that they are aware of it. E.g. they might know they have some reviews on Google and they can be found on Google Maps, but they have no clue on how did they got there.

Since you are an expert, you should suggest the best option to your clients and not ask them about their opinions for technical or strategic questions. Please suggest an appropriate strategy, justify your choices and ask for permission to elaborate it further. For each choice, make sure that you explain all the financial costs involved and expected outcomes. If there is no cost, make it clear.  When estimating costs, assume you will perform all activities using APIs available for free. Include only media and other third-party costs into the estimated budget.

Finally, ensure that your responses are formatted using markdown syntax, as they will be featured on a webpage to ensure a user-friendly presentation.
"""

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
@app.get("/login")
async def get_login_url(request: Request, user_id: int = Query(title="User ID")):
    user = await get_user(user_id=user_id)

    google_oauth_url = (
        f"{oauth2_settings['auth_uri']}?client_id={oauth2_settings['clientId']}"
        f"&redirect_uri={oauth2_settings['redirectUri']}&response_type=code"
        "&scope=https://www.googleapis.com/auth/adwords email"
        f"&access_type=offline&prompt=consent&state={user_id}"
    )
    return {"login_url": google_oauth_url}


# Route 2: Save user credentials/token to a JSON file
@app.get("/login/callback")
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
        "developer_token": "rQl20ooeSUSJsTIredWGFw",  # Replace with your actual developer token
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
@app.get("/list-accessible-customers")
async def list_accessible_customers(user_id: int = Query(title="User ID")):
    user_credentials = await load_user_credentials(user_id)
    client = create_google_ads_client(user_credentials)
    customer_service = client.get_service("CustomerService")
    accessible_customers = customer_service.list_accessible_customers()

    customer_ids = [x.split("/")[-1] for x in accessible_customers.resource_names]
    return customer_ids


# Route 4: Fetch user's ad campaign data
@app.get("/search")
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


async def get_openai_response(conversation: List[Dict[str, str]]):
    try:
        messages = [{"role": "system","content": SYSTEM_PROMPT}] + conversation
        completion = await azure_openai_client.chat.completions.create(
            model=client_secret_data["azure_openai"]["model"],
            messages= messages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    result = completion.choices[0].message.content
    return result

class AzureOpenAIRequest(BaseModel):
    conversation: List[Dict[str, str]]

# Route 5: Connect to OpenAI and get response
@app.post("/conversation")
async def create_item(request: AzureOpenAIRequest):
    conversation = request.conversation
    result = await get_openai_response(conversation)
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
