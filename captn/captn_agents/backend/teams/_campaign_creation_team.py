import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from ....google_ads.client import clean_nones
from ..config import Config
from ..tools._campaign_creation_team_tools import (
    AdGroupAdForCreation,
    AdGroupCriterionForCreation,
    AdGroupForCreation,
    AdGroupWithAdAndKeywords,
    create_campaign_creation_team_toolbox,
)
from ._shared_prompts import (
    MODIFICATION_FUNCTIONS_INSTRUCTIONS,
    REPLY_TO_CLIENT_COMMAND,
)
from ._team import Team

__all__ = ("CampaignCreationTeam",)


ad_group_ad = AdGroupAdForCreation(
    final_url="https://www.example.com",
    headlines=["headline1", "headline2", "headline3"],
    descriptions=["description1", "description2"],
    status="ENABLED",
)

keyword1 = AdGroupCriterionForCreation(
    keyword_text="keyword1",
    keyword_match_type="EXACT",
    status="ENABLED",
)
keyword2 = AdGroupCriterionForCreation(
    keyword_text="keyword2",
    keyword_match_type="EXACT",
    status="ENABLED",
)

ad_group = AdGroupForCreation(
    name="ad_group",
    status="ENABLED",
    ad_group_ad=ad_group_ad,
    keywords=[keyword1, keyword2],
)

ad_group_with_ad_and_keywords = AdGroupWithAdAndKeywords(
    customer_id="2222",
    campaign_id="1212",
    ad_group=ad_group,
    ad_group_ad=ad_group_ad,
    keywords=[keyword1, keyword2],
)

example_json = json.dumps(
    clean_nones(ad_group_with_ad_and_keywords.model_dump()), indent=2
)


@Team.register_team("campaign_creation_team")
class CampaignCreationTeam(Team):
    _functions: List[Dict[str, Any]] = []

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

    _retry_messages = [
        "NOTE: When generating JSON for the function, do NOT use ANY whitespace characters (spaces, tabs, newlines) in the JSON string.\n\nPlease continue.",
        f"Here is an example of a valid JSON string for the 'create_ad_group_with_ad_and_keywords': {example_json}",
        "Please continue.",
    ] * 2

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
        config_list: Optional[List[Dict[str, str]]] = None,
    ):
        recommended_modifications_and_answer_list: List[
            Tuple[Dict[str, Any], Optional[str]]
        ] = []
        function_map: Dict[str, Callable[[Any], Any]] = {}
        roles: List[Dict[str, str]] = CampaignCreationTeam._default_roles

        super().__init__(
            user_id=user_id,
            conv_id=conv_id,
            roles=roles,
            task=task,
            function_map=function_map,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
            use_user_proxy=True,
        )

        if config_list is None:
            config = Config()
            config_list = config.config_list_gpt_4

        self.llm_config = CampaignCreationTeam._get_llm_config(
            seed=seed, temperature=temperature, config_list=config_list
        )

        self._create_members()

        self._add_tools()

        self._create_initial_message()

    def _add_tools(self) -> None:
        self.toolbox = create_campaign_creation_team_toolbox(
            user_id=self.user_id,
            conv_id=self.conv_id,
            recommended_modifications_and_answer_list=self.recommended_modifications_and_answer_list,
        )
        for agent in self.members:
            if agent != self.user_proxy:
                self.toolbox.add_to_agent(agent, self.user_proxy)

    @property
    def _task(self) -> str:
        return f"""You are a Google Ads team in charge of CREATING digital campaigns.
The client has sent you the task to create a digital campaign for them. And this is the customer's brief:
\n{self.task}\n\n"""

    @property
    def _guidelines(self) -> str:
        return f"""## Guidelines
0. NEVER repeat yourself or previous messages.
1. BEFORE you do ANYTHING, write a detailed step-by-step plan of what you are going to do. For EACH STEP, an APPROPRIATE
TEAM MEMBER should propose a SOLUTION for that step. The TEAM MEMBER PROPOSING the solution should explain the
reasoning behind it (as short as possible), and every OTHER TEAM MEMBER on the team should give a CONSTRUCTIVE OPINION (also as short as possible). The TEAM MEMBER
proposing the ORIGINAL SOLUTION should take those considerations into account and adjust the SOLUTION accordingly.
Once the solution is modified, the team should REPEAT the process until the team reaches a CONSENSUS. The team should
then move on to the next step. If the team is unable to reach a consensus, the account manager should make the final
call. If you need additional information, use the 'reply_to_client' command to ask the client for it.
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
Use it only to retrieve the information about the currency and already existing campaigns, but do NOT waste time on retrieving the information which is not needed for the new campaign creation.
32. Ad Copy headlines can have MAXIMUM 30 characters and descriptions can have MAXIMUM 90 characters, NEVER suggest headlines/descriptions which exceed that length or you will be penalized!
33. If the client sends you invalid headline/description, do not try to modify it yourself! Explain the problems to him and suggest valid headline/description.
34. Ad rules:
- MINIMUM 3 and MAXIMUM 15 headlines.
- MINIMUM 2 and MAXIMUM 4 descriptions.
It is recommended to use the MAXIMUM number of headlines and descriptions. So if not explicitly told differently, suggest adding 15 headlines and 4 descriptions!
35. When replying to the client, try to finish the message with a question, that way you will navigate the client what to do next
36. Before setting any kind of budget, check the default currency from the customer table and convert the budget to that currency.
You can use the following query for retrieving the local currency: SELECT customer.currency_code FROM customer WHERE customer.id = '1212121212'
37. Finally, ensure that your responses are formatted using markdown syntax (except for the HTML anchor tags),
as they will be featured on a webpage to ensure a user-friendly presentation.

Here is a list of things which you CAN do:
- retrieve the information about your campaigns, ad groups, ads, keywords etc.
- create campaigns
- Create Ad Group, Ad and keywords by using the following command create_ad_group_with_ad_and_keywords
You can NOT do anything else, so do not suggest changes which you can NOT perform.
- e.g. you can NOT set Google ads targeting, negative keywords, ad extensions etc.


Example of the JSON input for the 'create_ad_group_with_ad_and_keywords' command:
{example_json}

When suggesting the JSON input, do NOT add \\n, \\t or any whitespaces to the JSON!!!

smart suggestions examples:
Use smart suggestions to suggest keywords, headlines, descriptions etc. which can be added/updated/removed. This feature is very useful for the client.
Do NOT use smart suggestions for open ended questions or questions which require the clients input.

When you ask the client for some suggestions (e.g. which headline should be added), you should also generate smart suggestions like:
"smart_suggestions": {{
    "suggestions":["Add headline x", "Add headline y", "Add headline z"],
    "type":"manyOf"
}}


VERY IMPORTANT NOTES:
The first and the MOST IMPORTANT thing is that you can NOT make any permanent changes without the clients approval!!!
Make sure that you explicitly tell the client which changes you want, which resource and attribute will be affected and wait for the permission!

This is a template which you should follow when you are asked to optimize campaigns:
The FIRST step should do is to analyze the received information about the client's business and his website.
- The SECOND step is recommending and creating a new campaign
- The THIRD step is recommending and creating new ad groups with ads and keywords
- Once you have created the campaign, ad groups, ads and keywords. Write a detailed summary about the campaign which you have created and tell the client that you have finished the task.
- If the client wants to make some changes/updates, tell him to create a new chat by clicking on the "New chat" and to ask for the changes/updates there.
"""  # nosec: [B608]

    @property
    def _commands(self) -> str:
        return f"""## Commands
All of the command use JSON input, when generating the command, make sure that the JSON is properly formatted.
Do NOT add \\n,\\t or any other whitespace characters in the JSON input. THIS IS THE MOST IMPORTANT THING!

All team members have access to the following command:
1. {REPLY_TO_CLIENT_COMMAND}
"smart_suggestions": {{
    'suggestions': ['Please make some headlines suggestions', 'Please make some descriptions suggestions'],
    'type': 'manyOf'
}}

2. ask_client_for_permission: Ask the client for permission to make the changes. Use this method before calling any of the modification methods!
params: (resource_details: str, function_name: str, modification_function_parameters: Dict[str, Any])
ALL parameters are mandatory, do NOT forget to include 'modification_function_parameters'!

You MUST use this before you make ANY permanent changes. ALWAYS use this command before you make any changes and do NOT use 'reply_to_client' command for asking the client for the permission to make the changes!

3. 'list_accessible_customers': List all the customers accessible to the client, no input params: ()

4. 'execute_query': Query Google ads API for the campaign information. Both input parameters are optional. params: (customer_ids: Optional[List[str]], query: Optional[str])
Example of customer_ids parameter: ["12", "44", "111"]

5. 'change_google_account': Generates a new login URL for the Google Ads API, params: ()
Use this command only if the client asks you to change the Google account. If there are some problems with the current account, first ask the client if he wants to use different account for his Google Ads.

{MODIFICATION_FUNCTIONS_INSTRUCTIONS}
6. 'create_campaign': Create new campaign, params: (customer_id: string, name: string, budget_amount_micros: int, local_currency: string, status: Optional[Literal["ENABLED", "PAUSED"]],
network_settings_target_google_search: Optional[boolean], network_settings_target_search_network: Optional[boolean], network_settings_target_content_network: Optional[boolean],
)
Before creating a new campaign, you must find out the local_currency from the customer table and convert the budget to that currency.
You can use the following query for retrieving the local currency: SELECT customer.currency_code FROM customer WHERE customer.id = '1212121212'
For creating a new campaign, the client must provide/approve the 'budget_amount_micros' and 'name'.
If the client specifies the 'budget_amount_micros' in another currency, you must convert it to the local currency!
Otherwise, incorrect budget will be set for the campaign!
When asking the client for the approval, you must explicitly tell him about the parameters which you are going to set by using the 'modification_function_parameters'
Otherwise, we will NOT be able to create a new campaign!

Here is an example of correct 'resource_details' parameter:
    Campaign name: xyz
    Daily budget: 3 EUR (budget_amount_micros will be set to 3000000)
    Currency: EUR
    Status: Enabled
    Targeting: Google Search Network and Google Display Network
    The campaign will focus on promoting your AI-powered framework and products such as FastStream and Monotonic Neural Networks.

7. 'create_ad_group_with_ad_and_keywords': Create Ad Group, Ad and keywords, params: (ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords)
When asking the client for the approval, you must explicitly tell him which final_url, headlines, descriptions and keywords you are going to set
NOTE: ad does NOT have a 'final_urls' attribute, only 'final_url' attribute! Please make sure that you set the 'final_url' attribute for the ad!
"""  # nosec: [B608]

    @classmethod
    def get_capabilities(cls) -> str:
        return """Campaign Creation Team capabilities:
This team is the BEST choice for creating NEW Google Ads campaigns and everything that comes with it.
- Get the information about the client's Google Ads account (campaigns, ad groups, ads, keywords etc.)
- Create new campaign
- Create new ad group
- Create new ad
- Create new keywords

The main benefit of this team is that they can create a new campaign from scratch QUICKLY.
But if you want to optimize an existing campaign or make some changes this is NOT the right team for you.
"""

    @classmethod
    def get_brief_template(cls) -> str:
        return """A structured customer brief, adhering to industry standards for a digital marketing campaign. You must fill in the following details based on the client's requirements:

Business:
Goal:
Current Situation:
Website:
Digital Marketing Objectives:
Next Steps:
Any Other Information Related to Customer Brief:
Budget: (recommended 3eur per day)


Not needed info:
- duration of the campaign
- target audience
- conversion tracking

Now Let's get all the information from the clients web page and create a detailed plan for the campaign.
"""
