from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from annotated_types import Len
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

from captn.captn_agents.backend.google_ads_team import (
    GoogleAdsTeam,
    get_campaign_creation_team_shared_functions,
)
from captn.captn_agents.backend.team import Team
from captn.google_ads.client import google_ads_create_update

from .function_configs import (
    ask_client_for_permission_config,
    change_google_account_config,
    create_ad_group_with_ad_and_keywords_config,
    create_campaign_config,
    execute_query_config,
    get_info_from_the_web_page_config,
    list_accessible_customers_config,
    properties_config,
    reply_to_client_2_config,
)


class CampaignCreationTeam(Team):
    _functions: List[Dict[str, Any]] = [
        ask_client_for_permission_config,
        change_google_account_config,
        create_campaign_config,
        execute_query_config,
        get_info_from_the_web_page_config,
        list_accessible_customers_config,
        reply_to_client_2_config,
        create_ad_group_with_ad_and_keywords_config,
    ]

    _default_roles = [
        {
            "Name": "Copywriter",
            "Description": "You are a Copywriter in the digital agency",
        },
        {
            "Name": "Account_manager",
            "Description": """You are an account manager in the digital agency.
You are also SOLELY responsible for communicating with the client.

Based on the initial task, a number of proposed solutions will be suggested by the team. You must ask the team to write a detailed plan
including steps and expected outcomes. Once the plan is ready, you must ask the client for permission to execute it using
'ask_client_for_permission'. Once the permission is granted, please instruct the team to execute the plan. Once the proposed solution
is executed, you must write down the accomplished work and forward it to the client using 'reply_to_client'.

Once the initial task given to the team is completed by implementing proposed solutions, you must write down the
accomplished work and execute the 'reply_to_client' command. That message will be forwarded to the client so make
sure it is understandable by non-experts.
""",
        },
    ]

    def __init__(
        self,
        *,
        task: str,
        user_id: int,
        conv_id: int,
        work_dir: str = "campaign_creation_team",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
    ):
        clients_question_answere_list: List[Tuple[str, Optional[str]]] = []
        function_map: Dict[str, Callable[[Any], Any]] = _get_function_map(
            user_id=user_id,
            conv_id=conv_id,
            work_dir=work_dir,
            clients_question_answere_list=clients_question_answere_list,
        )
        roles: List[Dict[str, str]] = CampaignCreationTeam._default_roles

        name = Team.get_user_conv_team_name(
            name_prefix=CampaignCreationTeam._get_team_name_prefix(),
            user_id=user_id,
            conv_id=conv_id,
        )

        super().__init__(
            roles=roles,
            function_map=function_map,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            name=name,
            clients_question_answere_list=clients_question_answere_list,
        )

        self.conv_id = conv_id
        self.task = task
        self.llm_config = CampaignCreationTeam.get_llm_config(
            seed=seed, temperature=temperature
        )

        self._create_members()
        self._create_initial_message()

    @staticmethod
    def _is_termination_msg(x: Dict[str, Optional[str]]) -> bool:
        return GoogleAdsTeam._is_termination_msg(x)

    @classmethod
    def _get_team_name_prefix(cls) -> str:
        return "campaign_creation_team"

    @property
    def _task(self) -> str:
        return f"""You are a Google Ads team in charge of CREATING digital campaigns.
The client has sent you the task to create a digital campaign for them. And this is the customer's brief:
\n{self.task}\n\n"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
1. Before solving the current task given to you, carefully write down all assumptions and ask any clarification
questions using the 'reply_to_client' function.
Also, if a Website is provided in the client brief, use the 'get_info_from_the_web_page' command to get the summary of the web page.
2. Once you have all the information you need, you must create a detailed step-by-step plan on how to solve the task.
3. If you receive a login url, forward it to the client by using the 'reply_to_client' function.
Do NOT use smart suggestions when forwarding the login url to the client!
4. Account_manager is responsible for coordinating all the team members and making sure the task is completed on time.
5. Please be concise and clear in your messages. As agents implemented by LLM, save context by making your answers as short as possible.
Don't repeat your self and others and do not use any filler words.
8. Do NOT use 'reply_to_client' command for asking the questions on how to Google Ads API nor for asking the client for the permission to make the changes (use 'ask_client_for_permission' command instead).
Your team is in charge of using the Google Ads API and no one else does NOT know how to use it.
10. Before making any changes, ask the client for approval.
Also, make sure that you explicitly tell the client which changes you want to make.
12. Never repeat the content from (received) previous messages
13. When referencing the customer ID, return customer.descriptive_name also or use a hyperlink to the Google Ads UI
14. The client can NOT see your conversation, he only receives the message which you send him by using the
'reply_to_client' or 'ask_client_for_permission' command
19. There is a list of commands which you are able to execute in the 'Commands' section.
You can NOT execute anything else, so do not suggest changes which you can NOT perform.
27. When you create a new campaign/ad group etc. create clickable link in the markdown format which will open a NEW tab in the Google Ads UI
Always return these kind of links in the EXACT following format: <a href="https://ads.google.com/aw/campaigns?campaignId=1212121212" target=\"_blank\">1212121212</a>
IMPORTANT: the page MUST be opened in the NEW Tab (do not forget 'target' parameter)!
31. When using 'execute_query' command, try to use as small query as possible and retrieve only the needed columns
32. Ad Copy headlines can have MAXIMUM 30 characters and descriptions can have MAXIMUM 90 characters, NEVER suggest headlines/descriptions which exceed that length or you will be penalized!
33. If the client sends you invalid headline/description, do not try to modify it yourself! Explain the problems to him and suggest valid headline/description.
34. Ad rules:
- MINIMUM 3 and MAXIMUM 15 headlines.
- MINIMUM 2 and MAXIMUM 4 descriptions.
It is recomended to use the MAXIMUM number of headlines and descriptions. So if not explicitly told differently, suggest adding 15 headlines and 4 descriptions!
36. When replying to the client, try to finish the message with a question, that way you will navigate the client what to do next
37. Use the 'get_info_from_the_web_page' command to get the summary of the web page. This command can be very useful for figuring out the clients business and what he wants to achieve.
e.g. if you know the final_url, you can use this command to get the summary of the web page and use it for SUGGESTING (NEVER modify without permision!) keywords, headlines, descriptions etc.
You can find most of the information about the clients business from the provided web page(s). So instead of asking the client bunch of questions, ask only for his web page(s)
and try get_info_from_the_web_page. Only if 'get_info_from_the_web_page' command does not provide you with enough information (or it fails), ask the client for the additional information about his business/web page etc.
40. Before setting any kind of budget, check the default currency from the customer table and convert the budget to that currency.
You can use the following query for retrieving the local currency: SELECT customer.currency_code FROM customer WHERE customer.id = '1212121212'
42. Finally, ensure that your responses are formatted using markdown syntax (except for the HTML anchor tags),
as they will be featured on a webpage to ensure a user-friendly presentation.

Here is a list of things which you CAN do:
- retrieve the information about your campaigns, ad groups, ads, keywords etc.
- create campaigns
- Create Ad Group, Ad and keywords by using the following command create_ad_group_with_ad_and_keywords

here is an example of how to use the create_ad_group_with_ad_and_keywords command:
ad_group_with_ad_and_keywords must be a json with the following structure:
{
  "customer_id": "1111",
  "campaign_id": "1212",
  "ad_group": {
    "customer_id": null,
    "status": "ENABLED",
    "campaign_id": null,
    "name": "ad_group",
    "cpc_bid_micros": null
  },
  "ad_group_ad": {
    "customer_id": null,
    "status": "ENABLED",
    "ad_group_id": null,
    "final_url": "https://www.example.com",
    "headlines": [
      "headline1",
      "headline2",
      "headline3"
    ],
    "descriptions": [
      "description1",
      "description2"
    ],
    "path1": null,
    "path2": null
  },
  "keywords": [
    {
      "customer_id": null,
      "status": "ENABLED",
      "ad_group_id": null,
      "keyword_text": "keyword1",
      "keyword_match_type": "EXACT"
    },
    {
      "customer_id": null,
      "status": "ENABLED",
      "ad_group_id": null,
      "keyword_text": "keyword2",
      "keyword_match_type": "EXACT"
    }
  ]
}
and two additional parameters:
- clients_approval_message: "yes"
- modification_question: "Can I make the following changes to your account?"


VERY IMPORTANT NOTES:
The first and the MOST IMPORTANT thing is that you can NOT make any permanent changes without the clients approval!!!
Make sure that you explicitly tell the client which changes you want, which resource and attribute will be affected and wait for the permission!

This is a template which you should follow when you are asked to optimize campaigns:
- The FIRST step should ALWAYS be retrieving the information about clients business by using 'get_info_from_the_web_page' command. If the client provides you some url, use this command to get the summary of the web page.
- The SECOND step is recommending and creating a new campaign
"""

    @property
    def _commands(self) -> str:
        return ""


def _get_function_map(
    user_id: int,
    conv_id: int,
    work_dir: str,
    clients_question_answere_list: List[Tuple[str, Optional[str]]],
) -> Dict[str, Any]:
    campaign_creation_team_shared_function_map = (
        get_campaign_creation_team_shared_functions(
            user_id=user_id,
            conv_id=conv_id,
            work_dir=work_dir,
            clients_question_answere_list=clients_question_answere_list,
        )
    )

    function_map = {
        "create_ad_group_with_ad_and_keywords": lambda ad_group_with_ad_and_keywords, clients_approval_message, modification_question: create_ad_group_with_ad_and_keywords(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
        )
    }
    function_map.update(campaign_creation_team_shared_function_map)
    return function_map


class AdBase(BaseModel):
    customer_id: Optional[
        Annotated[
            str, Field(..., description=properties_config["customer_id"]["description"])
        ]
    ] = None
    status: Annotated[
        Literal["ENABLED", "PAUSED"],
        Field(..., description="The status of the resource (ENABLED or PAUSED)"),
    ]


class AdGroupAd(AdBase):
    ad_group_id: Optional[
        Annotated[str, Field(..., description="Always set this field to None")]
    ] = None
    final_url: Annotated[
        str, Field(..., description=properties_config["final_url"]["description"])
    ]
    headlines: Annotated[
        List[Annotated[str, StringConstraints(max_length=30)]],
        Len(min_length=3, max_length=15),
    ]
    descriptions: Annotated[
        List[Annotated[str, StringConstraints(max_length=90)]],
        Len(min_length=2, max_length=4),
    ]
    path1: Optional[
        Annotated[
            str, Field(..., description=properties_config["path1"]["description"])
        ]
    ] = None
    path2: Optional[
        Annotated[
            str, Field(..., description=properties_config["path2"]["description"])
        ]
    ] = None


class AdGroupCriterion(AdBase):
    ad_group_id: Optional[
        Annotated[str, Field(..., description="Always set this field to None")]
    ] = None
    keyword_text: Annotated[
        str, Field(..., description=properties_config["keyword_text"]["description"])
    ]
    keyword_match_type: Annotated[
        Literal["EXACT", "BROAD", "PHRASE"],
        Field(..., description=properties_config["keyword_match_type"]["description"]),
    ]


class AdGroup(AdBase):
    campaign_id: Annotated[
        Optional[str],
        Field(..., description=properties_config["campaign_id"]["description"]),
    ] = None
    name: Annotated[str, Field(..., description="The name of the Ad Group")]
    cpc_bid_micros: Annotated[
        Optional[int], properties_config["cpc_bid_micros"]["description"]
    ] = None


class AdGroupWithAdAndKeywords(BaseModel):
    customer_id: Annotated[
        str, Field(..., description=properties_config["customer_id"]["description"])
    ]
    campaign_id: Annotated[
        str, Field(..., description=properties_config["campaign_id"]["description"])
    ]
    ad_group: AdGroup
    ad_group_ad: AdGroupAd
    keywords: List[AdGroupCriterion]


def _get_resource_id_from_response(response: str) -> str:
    return response.split("/")[-1].replace(".", "")


def create_ad_group_with_ad_and_keywords(
    user_id: int,
    conv_id: int,
    clients_question_answere_list: List[Tuple[str, Optional[str]]],
    # ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
    ad_group_with_ad_and_keywords: Dict[str, Any],
    clients_approval_message: Annotated[
        str, properties_config["clients_approval_message"]
    ],
    modification_question: Annotated[str, properties_config["modification_question"]],
) -> str:
    ad_group_with_ad_and_keywords_model = AdGroupWithAdAndKeywords(
        **ad_group_with_ad_and_keywords
    )
    ad_group = ad_group_with_ad_and_keywords_model.ad_group
    ad_group.customer_id = ad_group_with_ad_and_keywords_model.customer_id
    ad_group.campaign_id = ad_group_with_ad_and_keywords_model.campaign_id

    ad_group_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answere_list=clients_question_answere_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=ad_group,
        endpoint="/create-ad-group",
        skip_fields_check=True,
    )
    response = f"Ad group: {ad_group_response}\n"
    ad_group_id = _get_resource_id_from_response(ad_group_response)  # type: ignore

    ad_group_ad = ad_group_with_ad_and_keywords_model.ad_group_ad
    ad_group_ad.customer_id = ad_group_with_ad_and_keywords_model.customer_id
    ad_group_ad.ad_group_id = ad_group_id

    ad_group_ad_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answere_list=clients_question_answere_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=ad_group_ad,
        endpoint="/create-ad-group-ad",
        skip_fields_check=True,
    )
    response += f"Ad group ad: {ad_group_ad_response}\n"

    for keyword in ad_group_with_ad_and_keywords_model.keywords:
        keyword.customer_id = ad_group_with_ad_and_keywords_model.customer_id
        keyword.ad_group_id = ad_group_id
        keyword_response = google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=keyword,
            endpoint="/add-keywords-to-ad-group",
            skip_fields_check=True,
        )
        response += f"Keyword: {keyword_response}\n"

    return response
