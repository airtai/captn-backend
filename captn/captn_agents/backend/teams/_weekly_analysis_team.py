import ast
import json
import traceback
from collections import defaultdict
from datetime import datetime, timedelta
from os import environ
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union

import requests
from autogen.io import IOConsole, IOStream
from markdownify import markdownify as md
from prometheus_client import Counter
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt

from ....email.send_email import send_email as send_email_infobip
from ....google_ads.client import (
    ALREADY_AUTHENTICATED,
    execute_query,
    get_login_url,
    get_user_ids_and_emails,
    list_accessible_customers,
)
from ..config import Config
from ..tools._functions import get_webpage_status_code
from ..tools._weekly_analysis_team_tools import create_weekly_analysis_team_toolbox
from ._shared_prompts import GET_INFO_FROM_THE_WEB_COMMAND
from ._team import Team

__all__ = ("WeeklyAnalysisTeam",)

REACT_APP_API_URL = environ.get("REACT_APP_API_URL", "http://localhost:3001")
REDIRECT_DOMAIN = environ.get("REDIRECT_DOMAIN", "https://captn.ai")


class Metrics(BaseModel):
    impressions: int
    clicks: int
    interactions: int
    conversions: int
    cost_micros: int
    impressions_increase: Optional[float] = None
    clicks_increase: Optional[float] = None
    interactions_increase: Optional[float] = None
    conversions_increase: Optional[float] = None
    cost_micros_increase: Optional[float] = None


class KeywordMetrics(Metrics):
    historical_quality_score: Optional[int] = None
    historical_landing_page_quality_score: Optional[str] = None
    historical_creative_quality_score: Optional[str] = None
    historical_quality_score_increase: Optional[float] = None


class ResourceWithMetrics(BaseModel):
    id: str
    metrics: Metrics


class ResourceWithKeywordMetrics(BaseModel):
    id: str
    metrics: KeywordMetrics


class Keyword(ResourceWithKeywordMetrics):
    text: str
    match_type: str


class AdGroupAd(ResourceWithMetrics):
    final_urls: List[str]


class AdGroup(ResourceWithMetrics):
    name: str
    keywords: Dict[str, Keyword]
    ad_group_ads: Dict[str, AdGroupAd]


class Campaign(ResourceWithMetrics):
    name: str
    ad_groups: Dict[str, AdGroup]


class WeeklyCustomerReports(BaseModel):
    customer_id: str
    currency: str
    campaigns: Dict[str, Campaign]


class WeeklyReport(BaseModel):
    weekly_customer_reports: List[WeeklyCustomerReports]


def calculate_metrics_change(metrics1: Metrics, metrics2: Metrics) -> Metrics:
    return_metrics = {}
    for key, value in metrics1.__dict__.items():
        if key.endswith("_increase") or value is None:
            continue

        return_metrics[key] = value
        if isinstance(value, str):
            continue

        value2 = getattr(metrics2, key)
        if value == value2:
            return_metrics[key + "_increase"] = 0
        elif value == 0 or value2 == 0 or value2 is None:
            return_metrics[key + "_increase"] = None
        else:
            return_metrics[key + "_increase"] = round(
                (float(value - value2) / value2) * 100, 2
            )

    if isinstance(metrics1, KeywordMetrics):
        return KeywordMetrics(**return_metrics)

    return Metrics(**return_metrics)


@retry(stop=stop_after_attempt(3))
def google_ads_api_call(
    function: Union[
        Callable[[int, int, bool], Union[List[str], Dict[str, str]]],
        Callable[
            [int, int, Optional[str], Optional[List[str]], Optional[str]],
            Union[str, Dict[str, str]],
        ],
    ],
    **kwargs: Any,
) -> Any:
    return function(**kwargs)  # type: ignore


def get_weekly_keywords_report(
    user_id: int, conv_id: int, customer_id: str, date_query: str
) -> Dict[str, Dict[str, Keyword]]:
    query = (
        "SELECT ad_group.id, ad_group_criterion.criterion_id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, metrics.impressions, metrics.clicks, metrics.interactions, metrics.conversions, metrics.cost_micros, "
        "metrics.historical_quality_score, metrics.historical_landing_page_quality_score, metrics.historical_creative_quality_score "
        "FROM keyword_view "
        f"WHERE {date_query} AND campaign.status != 'REMOVED' AND ad_group.status != 'REMOVED' AND ad_group_criterion.status != 'REMOVED' "  # nosec: [B608]
    )
    query_result = google_ads_api_call(
        function=execute_query,
        user_id=user_id,
        conv_id=conv_id,
        customer_ids=[customer_id],
        query=query,
    )

    customer_results = ast.literal_eval(query_result)[customer_id]

    ad_group_keywords_dict: Dict[str, Dict[str, Keyword]] = defaultdict(dict)
    for customer_result in customer_results:
        historical_quality_score = (
            customer_result["metrics"]["historicalQualityScore"]
            if "historicalQualityScore" in customer_result["metrics"]
            else None
        )
        historical_landing_page_quality_score = (
            customer_result["metrics"]["historicalLandingPageQualityScore"]
            if "historicalLandingPageQualityScore" in customer_result["metrics"]
            else None
        )
        historical_creative_quality_score = (
            customer_result["metrics"]["historicalCreativeQualityScore"]
            if "historicalCreativeQualityScore" in customer_result["metrics"]
            else None
        )

        keyword = Keyword(
            id=customer_result["adGroupCriterion"]["criterionId"],
            text=customer_result["adGroupCriterion"]["keyword"]["text"],
            match_type=customer_result["adGroupCriterion"]["keyword"]["matchType"],
            metrics=KeywordMetrics(
                impressions=customer_result["metrics"]["impressions"],
                clicks=customer_result["metrics"]["clicks"],
                interactions=customer_result["metrics"]["interactions"],
                conversions=customer_result["metrics"]["conversions"],
                cost_micros=customer_result["metrics"]["costMicros"],
                historical_quality_score=historical_quality_score,
                historical_landing_page_quality_score=historical_landing_page_quality_score,
                historical_creative_quality_score=historical_creative_quality_score,
            ),
        )

        ad_group_keywords_dict[customer_result["adGroup"]["id"]][keyword.id] = keyword

    return ad_group_keywords_dict


def get_ad_groups_report(
    user_id: int, conv_id: int, customer_id: str, date_query: str
) -> Dict[str, Dict[str, AdGroup]]:
    query = (
        "SELECT campaign.id, ad_group.id, ad_group.name, metrics.impressions, metrics.clicks, metrics.interactions, metrics.conversions, metrics.cost_micros "
        "FROM ad_group "
        f"WHERE {date_query} AND campaign.status != 'REMOVED' AND ad_group.status != 'REMOVED'"  # nosec: [B608]
    )
    query_result = google_ads_api_call(
        function=execute_query,
        user_id=user_id,
        conv_id=conv_id,
        customer_ids=[customer_id],
        query=query,
    )
    customer_result = ast.literal_eval(query_result)[customer_id]

    keywords_report = get_weekly_keywords_report(
        user_id, conv_id, customer_id, date_query=date_query
    )
    ad_group_ads_report = get_weekly_ad_group_ads_report(
        user_id=user_id, conv_id=conv_id, customer_id=customer_id, date_query=date_query
    )
    campaign_ad_groups_dict: Dict[str, Dict[str, AdGroup]] = defaultdict(dict)

    for ad_group_result in customer_result:
        ad_group_id = ad_group_result["adGroup"]["id"]
        keywords = keywords_report.get(ad_group_id, {})
        ad_group_ads = ad_group_ads_report.get(ad_group_id, {})
        ad_group = AdGroup(
            id=ad_group_result["adGroup"]["id"],
            name=ad_group_result["adGroup"]["name"],
            metrics=Metrics(
                impressions=ad_group_result["metrics"]["impressions"],
                clicks=ad_group_result["metrics"]["clicks"],
                interactions=ad_group_result["metrics"]["interactions"],
                conversions=ad_group_result["metrics"]["conversions"],
                cost_micros=ad_group_result["metrics"]["costMicros"],
            ),
            keywords=keywords,
            ad_group_ads=ad_group_ads,
        )
        campaign_ad_groups_dict[ad_group_result["campaign"]["id"]][ad_group.id] = (
            ad_group
        )

    return campaign_ad_groups_dict


def get_campaigns_report(
    user_id: int, conv_id: int, customer_id: str, date_query: str
) -> Dict[str, Campaign]:
    query = (
        "SELECT campaign.id, campaign.name, metrics.impressions, metrics.clicks, metrics.interactions, metrics.conversions, metrics.cost_micros "
        "FROM campaign "
        f"WHERE {date_query} AND campaign.status != 'REMOVED'"  # nosec: [B608]
    )
    query_result = google_ads_api_call(
        function=execute_query,
        user_id=user_id,
        conv_id=conv_id,
        customer_ids=[customer_id],
        query=query,
    )
    customer_result = ast.literal_eval(query_result)[customer_id]
    campaigns: Dict[str, Campaign] = {}
    if not customer_result:
        return campaigns

    ad_groups_report = get_ad_groups_report(user_id, conv_id, customer_id, date_query)
    for campaign_result in customer_result:
        ad_groups = ad_groups_report.get(campaign_result["campaign"]["id"], {})
        campaign = Campaign(
            id=campaign_result["campaign"]["id"],
            name=campaign_result["campaign"]["name"],
            metrics=Metrics(
                impressions=campaign_result["metrics"]["impressions"],
                clicks=campaign_result["metrics"]["clicks"],
                interactions=campaign_result["metrics"]["interactions"],
                conversions=campaign_result["metrics"]["conversions"],
                cost_micros=campaign_result["metrics"]["costMicros"],
            ),
            ad_groups=ad_groups,
        )

        campaigns[campaign.id] = campaign

    return campaigns


def get_weekly_ad_group_ads_report(
    user_id: int, conv_id: int, customer_id: str, date_query: str
) -> Dict[str, Dict[str, AdGroupAd]]:
    query = (
        "SELECT ad_group.id, ad_group_ad.ad.id, ad_group_ad.ad.final_urls, metrics.impressions, metrics.clicks, metrics.interactions, metrics.conversions, metrics.cost_micros "
        "FROM ad_group_ad "
        f"WHERE {date_query} AND ad_group.status != 'REMOVED' AND ad_group_ad.status != 'REMOVED'"  # nosec: [B608]
    )
    query_result = google_ads_api_call(
        function=execute_query,
        user_id=user_id,
        conv_id=conv_id,
        customer_ids=[customer_id],
        query=query,
    )
    customer_result = ast.literal_eval(query_result)[customer_id]

    ad_group_ads_dict: Dict[str, Dict[str, AdGroupAd]] = defaultdict(dict)
    for ad_group_ad_result in customer_result:
        ad_group_ad = AdGroupAd(
            id=ad_group_ad_result["adGroupAd"]["ad"]["id"],
            final_urls=ad_group_ad_result["adGroupAd"]["ad"]["finalUrls"],
            metrics=Metrics(
                impressions=ad_group_ad_result["metrics"]["impressions"],
                clicks=ad_group_ad_result["metrics"]["clicks"],
                interactions=ad_group_ad_result["metrics"]["interactions"],
                conversions=ad_group_ad_result["metrics"]["conversions"],
                cost_micros=ad_group_ad_result["metrics"]["costMicros"],
            ),
        )
        ad_group_ads_dict[ad_group_ad_result["adGroup"]["id"]][ad_group_ad.id] = (
            ad_group_ad
        )

    return ad_group_ads_dict


def _calculate_update_metrics(
    resource_id: str,
    report: Union[ResourceWithMetrics, ResourceWithKeywordMetrics],
    report_yesterday: Dict[str, Union[ResourceWithMetrics, ResourceWithKeywordMetrics]],
) -> None:
    if resource_id not in report_yesterday:
        return
    report.metrics = calculate_metrics_change(
        report.metrics, report_yesterday[resource_id].metrics
    )


def compare_reports(
    report: Dict[str, Campaign],
    report_yesterday: Dict[str, Campaign],
) -> Dict[str, Campaign]:
    for campaign_id, campaign in report.items():
        _calculate_update_metrics(campaign_id, campaign, report_yesterday)  # type: ignore
        for ad_group_id, ad_group in campaign.ad_groups.items():
            _calculate_update_metrics(
                ad_group_id,
                ad_group,
                report_yesterday[campaign_id].ad_groups,  # type: ignore
            )
            for keyword_id, keyword in ad_group.keywords.items():
                _calculate_update_metrics(
                    keyword_id,
                    keyword,
                    report_yesterday[campaign_id].ad_groups[ad_group_id].keywords,  # type: ignore
                )
            for ad_group_ad_id, ad_group_ad in ad_group.ad_group_ads.items():
                _calculate_update_metrics(
                    ad_group_ad_id,
                    ad_group_ad,
                    report_yesterday[campaign_id].ad_groups[ad_group_id].ad_group_ads,  # type: ignore
                )

    return report


def _create_date_query(date: str, week: Literal["THIS", "LAST"]) -> str:
    datetime_date = datetime.strptime(date, "%Y-%m-%d").date()

    if week == "THIS":
        six_days_before = (datetime_date - timedelta(6)).isoformat()
        query = f"segments.date BETWEEN '{six_days_before}' AND '{date}'"
    elif week == "LAST":
        seven_days_before = (datetime_date - timedelta(7)).isoformat()
        thirteen_days_before = (datetime_date - timedelta(13)).isoformat()
        query = (
            f"segments.date BETWEEN '{thirteen_days_before}' AND '{seven_days_before}'"
        )
    else:
        raise ValueError("Invalid week value. Must be 'THIS' or 'LAST'.")
    return query


def get_weekly_report_for_customer(
    user_id: int, conv_id: int, customer_id: str, date: str
) -> WeeklyCustomerReports:
    this_week_query = _create_date_query(date, "THIS")
    campaigns_report = get_campaigns_report(
        user_id, conv_id, customer_id, this_week_query
    )

    last_week_query = _create_date_query(date, "LAST")
    last_week_campaigns_report = get_campaigns_report(
        user_id, conv_id, customer_id, last_week_query
    )

    compared_campaigns_report = compare_reports(
        campaigns_report, last_week_campaigns_report
    )

    query = "SELECT customer.currency_code FROM customer"
    query_result = google_ads_api_call(
        function=execute_query,
        user_id=user_id,
        conv_id=conv_id,
        customer_ids=[customer_id],
        query=query,
    )
    currency = ast.literal_eval(query_result)[customer_id][0]["customer"][
        "currencyCode"
    ]
    return WeeklyCustomerReports(
        customer_id=customer_id, currency=currency, campaigns=compared_campaigns_report
    )


WARNING_DESCRIPTION = "Some final URLs for your Ads are not reachable:"


def get_web_status_code_report_for_campaign(
    campaign: Dict[str, Any], customer_id: str
) -> Tuple[Optional[str], List[str]]:
    warning_message = f"<li><strong>WARNING:</strong>{WARNING_DESCRIPTION}\n<ul>\n"
    warning_messages_list: List[str] = []
    send_warning_message_for_campaign = False

    for ad_group_id, ad_group in campaign["ad_groups"].items():
        for ad_group_ad_id, ad_group_ad in ad_group["ad_group_ads"].items():
            final_urls = ad_group_ad["final_urls"]
            for final_url in final_urls:
                status_code = get_webpage_status_code(url=final_url)
                if status_code is None or status_code < 200 or status_code >= 400:
                    send_warning_message_for_campaign = True
                    final_url_link = (
                        f"<a href='{final_url}' target='_blank'>{final_url}</a>"
                    )
                    google_ads_link = f"<a href='https://ads.google.com/aw/ads/edit/search?adId={ad_group_ad_id}&adGroupIdForAd={ad_group_id}&__e={customer_id}' target='_blank'>{ad_group_ad_id}</a>"
                    current_warning_message = f"<li>Final url {final_url_link} used in Ad {google_ads_link} is <strong>not reachable</strong></li>\n"
                    warning_messages_list.append(current_warning_message)
                    warning_message += current_warning_message

    warning_message += "</ul>\n</li>\n"
    return (
        (warning_message, warning_messages_list)
        if send_warning_message_for_campaign
        else (None, [])
    )


EMAIL_TEMPLATES_PATH = (
    Path(__file__).parent.parent.parent.parent.parent.absolute() / "templates" / "email"
)
with open(str(EMAIL_TEMPLATES_PATH / "main_email_template.html")) as file:
    MAIN_EMAIL_TEMPLATE = file.read()
with open(str(EMAIL_TEMPLATES_PATH / "customer_report_template.html")) as file:
    CUSTOMER_REPORT_TEMPLATE = file.read()
with open(str(EMAIL_TEMPLATES_PATH / "campaigns_template.html")) as file:
    CAMPAIGNS_TEMPLATE = file.read()
with open(str(EMAIL_TEMPLATES_PATH / "campaign_warning_template.html")) as file:
    CAMPAIGN_WARNING_TEMPLATE = file.read()
with open(str(EMAIL_TEMPLATES_PATH / "proposed_action.html")) as file:
    PROPOSED_ACTION_TEMPLATE = file.read()


def _add_metrics_message(
    title: str,
    metrics: Dict[str, Optional[Union[int, float]]],
    field: str,
    currency: str = "",
) -> Tuple[str, str, str]:
    if field == "cost_micros":
        value = round(metrics[field] / 1000000, 2)  # type: ignore
    else:
        value = metrics[field]  # type: ignore

    increase = metrics[field + "_increase"]
    if increase is None:
        return (f"<li>{title}: {value}</li>", str(value), "-")

    if increase >= 0:
        is_increase = f"+{increase}%"
    else:
        is_increase = f"{increase}%"

    if currency:
        currency = f" {currency}"
    value_with_currency = f"{value}{currency}"
    return (
        f"<li>{title}: {value_with_currency} ({is_increase})</li>",
        value_with_currency,
        is_increase,
    )


def _update_message_and_campaigns_template(
    title: str,
    metrics: Dict[str, Optional[Union[int, float]]],
    field: str,
    message: str,
    campaigns_template: str,
    currency: str = "",
) -> Tuple[str, str]:
    message_for_metric, value_with_currency, is_increase = _add_metrics_message(
        title=title, metrics=metrics, field=field, currency=currency
    )
    message += message_for_metric
    campaigns_template = campaigns_template.replace(f"{{{field}}}", value_with_currency)
    campaigns_template = campaigns_template.replace(
        f"{{{field}_change_rate}}", is_increase
    )

    return message, campaigns_template


def construct_weekly_report_email_from_template(
    weekly_reports: Dict[str, Any], date: str
) -> Tuple[str, str]:
    main_email_template = MAIN_EMAIL_TEMPLATE
    main_email_template = main_email_template.replace("{todays_date}", date)
    customers_section = ""

    message = f"<h2>Weekly Google Ads Performance Report - {date}</h2>"
    message += "<p>We're here with your weekly analysis of your Google Ads campaigns. Below, you'll find insights into your campaign performances, along with notable updates and recommendations for optimization.</p>"
    campaigns_report = weekly_reports["weekly_customer_reports"]
    for customer_report in campaigns_report:
        customer_report_template = CUSTOMER_REPORT_TEMPLATE

        customer_id = customer_report["customer_id"]
        customer_report_template = customer_report_template.replace(
            "{customer_id}", customer_report["customer_id"]
        )
        currency = customer_report["currency"]
        message += f"<p>Customer <strong>{customer_id}</strong></p>"
        message += "<ul>"

        campaigns_section = ""
        for _, campaign in customer_report["campaigns"].items():
            campaigns_template = CAMPAIGNS_TEMPLATE

            campaign_name = campaign["name"]
            campaigns_template = campaigns_template.replace(
                "{campaign_name}", campaign_name
            )

            link_to_campaign = f"https://ads.google.com/aw/campaigns?campaignId={campaign['id']}&__e={customer_id}"
            message += f"<li>Campaign <strong><a href='{link_to_campaign}' target='_blank'>{campaign_name}</a></strong>"
            message += "<ul>"

            update_list = [
                ("Clicks", "clicks", ""),
                ("Conversions", "conversions", ""),
                ("Cost", "cost_micros", currency),
            ]
            for title, field, currency in update_list:
                message, campaigns_template = _update_message_and_campaigns_template(
                    title=title,
                    metrics=campaign["metrics"],
                    field=field,
                    message=message,
                    campaigns_template=campaigns_template,
                    currency=currency,
                )

            (
                warning_message,
                warning_messages_list,
            ) = get_web_status_code_report_for_campaign(campaign, customer_id)
            if warning_message:
                campaign_warning_template = CAMPAIGN_WARNING_TEMPLATE
                campaign_warning_template = campaign_warning_template.replace(
                    "{warning_description}", WARNING_DESCRIPTION
                )
                campaign_warning_template = campaign_warning_template.replace(
                    "{warning_list}", "".join(warning_messages_list)
                )
                message += warning_message

            if warning_message:
                campaigns_template = campaigns_template.replace(
                    "{campaign_warnings}", campaign_warning_template
                )
            else:
                campaigns_template = campaigns_template.replace(
                    "{campaign_warnings}", ""
                )

            campaigns_section += campaigns_template
            message += "</ul></li>"
        message += "</ul>"

        customer_report_template = customer_report_template.replace(
            "{campaigns}", campaigns_section
        )
        customers_section += customer_report_template

    main_email_template = main_email_template.replace(
        "{customers_report}", customers_section
    )

    return message, main_email_template


def _check_if_any_campaign_exists(weekly_report: WeeklyReport) -> bool:
    for weekly_customer_report in weekly_report.weekly_customer_reports:
        if weekly_customer_report.campaigns:
            return True
    return False


def get_weekly_report(date: str, user_id: int, conv_id: int) -> Optional[str]:
    customer_ids: List[str] = google_ads_api_call(
        function=list_accessible_customers,
        user_id=user_id,
        conv_id=conv_id,
        get_only_non_manager_accounts=True,
    )
    weekly_customer_reports = [
        get_weekly_report_for_customer(
            user_id=user_id, conv_id=conv_id, customer_id=customer_id, date=date
        )
        for customer_id in customer_ids
    ]
    weekly_report = WeeklyReport(weekly_customer_reports=weekly_customer_reports)

    if not _check_if_any_campaign_exists(weekly_report):
        print(
            f"No campaigns found for the date {date}, user_id: {user_id}, conv_id: {conv_id}"
        )
        return None

    return weekly_report.model_dump_json(indent=2)


class WeeklyAnalysisTeam(Team):
    _functions: List[Dict[str, Any]] = []

    _shared_system_message = (
        "You have a strong SQL knowledge (and very experienced with postgresql)."
        "When sending an email, include all the findings you have and do NOT try to summarize the finding (too much info is better then too little), it will help the client to understand the problem and make decisions."
        "When analysing, start with simple queries and use more complex ones only if needed"
    )

    _default_roles = [
        {
            "Name": "Google_ads_specialist",
            "Description": f"""{_shared_system_message}
Your job is to suggest and execute the command from the '## Commands' section when you are asked to.""",
        },
        {
            "Name": "Copywriter",
            "Description": f"""You are a Copywriter in the digital agency
{_shared_system_message}""",
        },
        {
            "Name": "Digital_strategist",
            "Description": f"""You are a digital strategist in the digital agency
{_shared_system_message}""",
        },
        {
            "Name": "Account_manager",
            "Description": f"""You are an account manager in the digital agency.
{_shared_system_message}
and make sure the task is completed on time. You are also SOLELY responsible for communicating with the client.

Based on the initial task, a number of proposed solutions will be suggested by the team. You must ask the team to write a detailed plan
including steps and expected outcomes. Once the plan is ready, you must ask the client for permission to execute it using
'send_email'.

Once the initial task given to the team is completed by implementing proposed solutions, you must write down the
accomplished work and execute the 'send_email' command. That message will be forwarded to the client so make
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
        work_dir: str = "weekly_analysis",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
        config_list: Optional[List[Dict[str, str]]] = None,
    ):
        function_map: Dict[str, Callable[[Any], Any]] = {}
        roles: List[Dict[str, str]] = WeeklyAnalysisTeam._default_roles

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
            use_user_proxy=True,
        )

        if config_list is None:
            config = Config()
            config_list = config.config_list_gpt_4o

        self.llm_config = WeeklyAnalysisTeam._get_llm_config(
            seed=seed, temperature=temperature, config_list=config_list
        )

        self._create_members()

        self._add_tools()

        self._create_initial_message()

    def _add_tools(self) -> None:
        self.toolbox = create_weekly_analysis_team_toolbox(
            user_id=self.user_id,
            conv_id=self.conv_id,
            recommended_modifications_and_answer_list=self.recommended_modifications_and_answer_list,
        )
        for agent in self.members:
            if agent != self.user_proxy:
                self.toolbox.add_to_agent(agent, self.user_proxy)

    @property
    def _task(self) -> str:
        return f"""You are a Google Ads team in charge of running weekly analysis for the digital campaigns.
The client has sent you the following task:
\n{self.task}\n\n"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
1. Before solving the current task given to you, carefully write down all assumptions and discuss them within the team.
2. Once you have all the information you need, you must create a detailed step-by-step plan on how to solve the task.
3. If you receive a login url, forward it to the client by using the 'send_email' function.
If the user isn't logged in, we will NOT be able to access the Google Ads API.
4. Account_manager is responsible for coordinating all the team members and making sure the task is completed on time.
5. Please be concise and clear in your messages. As agents implemented by LLM, save context by making your answers as short as possible.
Don't repeat your self and others and do not use any filler words.
6. DO NOT USE execute_query command for retrieving Google Ads metrics! Otherwise you will be penalized!
7. Use the 'execute_query' command for finding the necessary information about the campaigns, ad groups, ads, keywords etc.
Do NOT use 'execute_query' command for retrieving Google Ads metrics (impressions, clicks, conversions, cost_micros etc.)!

7. Do not give advice on campaign improvement before you fetch all the important information about it by using 'execute_query' command.
8. You can NOT ask the client anything!
9. Never repeat the content from (received) previous messages
10. When referencing the customer ID, return customer.descriptive_name also or use a hyperlink to the Google Ads UI.
11. The client can NOT see your conversation, he only receives the message which you send him by using the
'send_email' command
Here an example on how to use the 'send_email' command:
'proposed_user_actions' must contain a list with MIN 1 and MAX 3 strings. We suggest to use the MAXIMUM number of proposed actions.
{"actions": {
    "proposed_user_actions": ["Remove 'Free' keyword because it is not performing well", "Increase budget from $10/day to $20/day",
    "Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'", "Select some or all of them"]
}}

propose_user_actions should NOT be general, but specific.
'proposed_user_actions' BAD EXAMPLES:
"Review the negative keywords in the campaigns to ensure they are not overly restrictive." is NOT specific enough.
"Conduct a keyword analysis to check if the current keywords are too restrictive or irrelevant, which could be leading to low ad visibility" is NOT specific enough.
"Consider enabling paused ad groups and ads if they are relevant and could contribute to campaign performance." is NOT specific enough.

propose_user_actions should never suggest to the client "Analyze" or "Review" something, because that is what we are doing! Based on our analysis, we should suggest to the client what to do!
These suggestions should be specific and actionable.
'proposed_user_actions' GOOD EXAMPLES:
"Remove 'Free' keyword because it is not performing well" is specific enough.
"Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'" is specific enough.

Messages within the 'proposed_user_actions' are the ONLY messages the client will see. So make sure to include all the necessary information in them.
e.g. Do NOT suggest 'Update the ad copy with the suggested headlines and descriptions for better engagement.' because the client will not know which ad copy you are talking about and what changes you want to make.

12. There is a list of commands which you are able to execute in the 'Commands' section.
You can NOT execute anything else, so do not suggest changes which you can NOT perform.

Do NOT suggest making changes of the following things, otherwise you will be penalized:
- Targeting settings
- Ad Extensions
- Budgeting
- Ad Scheduling

14. You can retrieve negative keywords from the 'campaign_criterion' table (so do not just check the
'ad_group_criterion' table and give up if there are not in that table)
15. Whenever you want to mention the ID of some resource (campaign, ad group, ad, keyword etc.), you must also mention the name of that resource.
e.g. "The campaign with ID 1234567890 and name 'Campaign 1' has ...". Otherwise, the client will not know which resource you are talking about!
16. Your clients are NOT experts and they do not know how to optimize Google Ads. So when you retrieve information about their campaigns, ads, etc.,
suggest which changes could benefit them
17. Do not overwhelm the client with unnecessary information. You must explain why you want to make some changes,
but the client does NOT need to know all the Google Ads details that you have retrieved
18. When using 'execute_query' command, try to use as small query as possible and retrieve only the needed columns
19. Ad Copy headlines can have MAXIMUM 30 characters and descriptions can have MAXIMUM 90 characters, NEVER suggest headlines/descriptions which exceed that length or you will be penalized!
20. Ad rules:
- MINIMUM 3 and MAXIMUM 15 headlines.
- MINIMUM 2 and MAXIMUM 4 descriptions.
It is recommended to use the MAXIMUM number of headlines and descriptions. So if not explicitly told differently, suggest adding 15 headlines and 4 descriptions!
21. Use the 'get_info_from_the_web_page' command to get the summary of the web page. This command can be very useful for figuring out the clients business and what he wants to achieve.
e.g. if you know the final_url, you can use this command to get the summary of the web page and use it for SUGGESTING keywords, headlines, descriptions etc.
You can find most of the information about the clients business from the provided web page(s). So instead of asking the client bunch of questions, ask only for his web page(s)
and try get_info_from_the_web_page.
22. Use 'get_info_from_the_web_page' when you want to retrieve the information about some product, category etc. from the clients web page.
e.g. if you want to retrieve the information about the TVs and you already know the url of the TVs section, you can use this command to get the summary of that web page section.
By doing that, you will be able to recommend MUCH BETTER keywords, headlines, descriptions etc. to the client.
21. Before suggesting any kind of budget, check the default currency from the customer table and convert the budget to that currency.
You can use the following query for retrieving the local currency: SELECT customer.currency_code FROM customer WHERE customer.id = '1212121212'
as they will be featured on a webpage to ensure a user-friendly presentation.
23. Once you have completed weekly analysis, you must send a summary of the work done to the client by using the 'send_email' command.

Here is a list of things which you CAN do after the client responds to your email.
So please recommend some of these changes to the client by using the 'actions' parameter in the 'send_email' command:
- update the status (ENABLED / PAUSED) of the campaign, ad group and ad
- create/update/remove headlines and descriptions in the Ad Copy. Make sure to follow the restrictions for the headlines and descriptions (MAXIMUM 30 characters for headlines and MAXIMUM 90 characters for descriptions)
- create/update/remove new keywords
- create/update/remove campaign/ ad group / ad / positive and negative keywords

Do NOT suggest making changes of the following things:
- Targeting settings
- Ad Extensions
- Budget updates (increase/decrease)
- Ad Scheduling

VERY IMPORTANT NOTES:
Make sure that you explicitly tell the client which changes you want, which resource and attribute will be affected.
This rule applies to ALL the commands which make permanent changes (create/update/delete)!!!

Try to figure out as much as possible before sending the email to the client. If you do not know something, ask the team members for help.
- analyse keywords and find out which are (i)relevant for clients business and suggest some create/update/remove actions
- Take a look at ad copy (headlines, descriptions, urls...) and make suggestions on what should be changed (create/update/remove headlines etc.)
- Headlines can have MAXIMUM 30 characters and description can have MAXIMUM 90 characters, NEVER suggest headlines/descriptions which exceed that length!
"""

    @property
    def _commands(self) -> str:
        return f"""## Commands
Never use functions.function_name(...) because functions module does not exist.
Just suggest calling function 'function_name'.

All team members have access to the following command:
1. send_email: Send email to the client, params: (actions: Actions(BaseModel))
Each message in the actions.proposed_user_actions parameter must contain all information useful to the client, because the client does not see your team's conversation
As we send this message to the client, pay attention to the content inside it. We are a digital agency and the messages we send must be professional.
2. {GET_INFO_FROM_THE_WEB_COMMAND}

ONLY Google ads specialist can suggest following commands:
1. 'list_accessible_customers': List all the customers accessible to the client, no input params: ()
2. 'execute_query': Query Google ads API for the campaign information. Both input parameters are optional. params: (customer_ids: Optional[List[str]], query: Optional[str])
Example of customer_ids parameter: ["12", "44", "111"]
You can use optional parameter 'query' for writing SQL queries.
Do NOT try to JOIN tables, otherwise you will be penalized!
Do NOT try to use multiple tables in the FROM clause (e.g. FROM ad_group_ad, ad_group, campaign), otherwise you will be penalized!

If you want to get negative keywords, use "WHERE campaign_criterion.negative=TRUE" for filtering.
Do NOT retrieve information about the REMOVED resources (campaigns, ad groups, ads...)!
Always add the following condition to your query: "WHERE campaign.status != 'REMOVED' AND ad_group.status != 'REMOVED' AND ad_group_ad.status != 'REMOVED'"
Here is few useful queries:
SELECT campaign.id, campaign.name, ad_group.id, ad_group.name, ad_group_ad.ad.id FROM ad_group_ad
SELECT ad_group_criterion.criterion_id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.negative FROM ad_group_criterion WHERE ad_group_criterion.ad_group = 'customers/2324127278/adGroups/161283342474'
SELECT campaign_criterion.criterion_id, campaign_criterion.type, campaign_criterion.keyword.text, campaign_criterion.negative FROM campaign_criterion WHERE campaign_criterion.campaign = 'customers/2324127278/campaigns/20978334367' AND campaign_criterion.negative=TRUE"

NEVER USE 'JOIN' in your queries, otherwise you will be penalized!
You can execute the provided queries ONLY by using the 'execute_query' command!
"""  # nosec: [B608]


def _create_final_html_message(
    main_email_template: str, proposed_user_action: List[str], conv_uuid: str
) -> str:
    proposed_user_actions_section = ""
    proposed_action_template = PROPOSED_ACTION_TEMPLATE

    for i, action in enumerate(proposed_user_action):
        proposed_user_actions_section += f"<li>{action} (<a href='{REDIRECT_DOMAIN}/chat/{conv_uuid}?selected_user_action={i+1}'>Link</a>)</li>"

    proposed_action_template = proposed_action_template.replace(
        "{proposed_actions_li_tags}", proposed_user_actions_section
    )
    main_email_template = main_email_template.replace(
        "{proposed_action}", proposed_action_template
    )

    return main_email_template


def _update_chat_message_and_send_email(
    user_id: int,
    conv_id: int,
    conv_uuid: str,
    client_email: str,
    messages: str,
    initial_message_in_chat: str,
    main_email_template: str,
    proposed_user_action: List[str],
) -> None:
    markdown = f"""<div class = "captn-daily-analysis">
{md(initial_message_in_chat)}
</div>
"""

    data = {
        "userId": user_id,
        "chatId": conv_id,
        "messages": messages,
        "initial_message_in_chat": markdown,
        "email_content": "<html></html>",
        "proposed_user_action": proposed_user_action,
    }

    response = requests.post(
        f"{REACT_APP_API_URL}/captn-daily-analysis-webhook", json=data, timeout=60
    )

    if response.status_code != 200:
        raise ValueError(response.content)

    main_email_template = _create_final_html_message(
        main_email_template, proposed_user_action, conv_uuid
    )

    send_email_infobip(
        to_email=client_email,
        subject="Capt’n.ai Weekly Analysis",
        body_text=main_email_template,
    )


def _get_conv_id_and_uuid(user_id: int, email: str) -> Tuple[int, str]:
    data = {"userId": user_id}

    response = requests.post(
        f"{REACT_APP_API_URL}/create-chat-webhook", json=data, timeout=60
    )
    if response.status_code != 200:
        ValueError(f"Wasn't able to create chat for user_id: {user_id} - email {email}")

    conv_id = response.json()["chatId"]
    conv_uuid = response.json()["chatUUID"]
    return conv_id, conv_uuid


def _delete_chat_webhook(user_id: int, conv_id: int) -> None:
    try:
        data = {
            "userId": user_id,
            "chatId": conv_id,
        }
        requests.post(f"{REACT_APP_API_URL}/delete-chat-webhook", json=data, timeout=60)
    except Exception as e:
        print(e)


def _create_task_message(
    date: str, weekly_reports: str, weekly_report_message: str
) -> str:
    task = f"""
You need to perform Google Ads Analysis for date: {date}.

Check which ads have the highest cost and which have the highest number of conversions.
If for some reason thera are no recorded impressions/clicks/interactions/conversions for any of the ads across all campaigns try to identify the reason (bad positive/negative keywords etc).
At the end of the analysis, you need to suggest the next steps to the client. Usually, the next steps are:
- pause the ads with the highest cost and the lowest number of conversions.
- keywords analysis (add negative keywords, add positive keywords, change match type etc).
- ad copy analysis (change the ad copy, add more ads etc).

I have prepared you a JSON file with the weekly report for the wanted date. Use it to suggest the next steps to the client.
{weekly_reports}


Here is also a HTML summary of the weekly report which will be sent to the client:
{weekly_report_message}

Please propose the next steps and send the email to the client.
"""
    return task


WEEKLY_ANALYSIS_TEAM_CONVERSATION_SUCCESS_TOTAL = Counter(
    "weekly_analysis_team_conversation_success_total",
    "Total count of successfully executed weekly analysis",
)


def _validate_conversation_and_send_email(
    weekly_analysis_team: WeeklyAnalysisTeam,
    conv_uuid: str,
    email: str,
    weekly_report_message: str,
    main_email_template: str,
) -> None:
    last_message = weekly_analysis_team.get_last_message(add_prefix=False)

    messages_list = weekly_analysis_team.get_messages()
    check_if_send_email = messages_list[-2]
    if (
        "tool_calls" in check_if_send_email
        and check_if_send_email["tool_calls"][0]["function"]["name"] == "send_email"
    ):
        if len(messages_list) < 3:
            messages = "[]"
        else:
            # Don't include the first message (task) and the last message (send_email)
            messages = json.dumps(messages_list[1:-1])
        last_message_json = json.loads(last_message)
        _update_chat_message_and_send_email(
            user_id=weekly_analysis_team.user_id,
            conv_id=weekly_analysis_team.conv_id,
            conv_uuid=conv_uuid,
            client_email=email,
            messages=messages,
            initial_message_in_chat=weekly_report_message,
            main_email_template=main_email_template,
            proposed_user_action=last_message_json["proposed_user_action"],
        )
        WEEKLY_ANALYSIS_TEAM_CONVERSATION_SUCCESS_TOTAL.inc()
    else:
        raise ValueError(
            f"Send email function is not called for user_id: {weekly_analysis_team.user_id} - email {email}!"
        )


WEEKLY_ANALYSIS_TEAM_CONVERSATIONS_TOTAL = Counter(
    "weekly_analysis_team_conversations_total",
    "Total count of executed weekly analysis (team conversation started)",
)


WEEKLY_ANALYSIS_EXCEPTIONS_TOTAL = Counter(
    "weekly_analysis_exceptions_total",
    "Total count of weekly analysis exceptions",
)

SKIPPED_USERS_TOTAL = Counter(
    "skipped_users_total",
    "Total count of users that were skipped during weekly analysis",
)


def _get_day_of_week(date_str: str) -> str:
    # Parse the date string into a datetime object
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # Get the day of the week as an integer (0=Monday, 6=Sunday)
    day_of_week_num = date_obj.weekday()

    # Map the integer to the day name
    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    day_of_week_name = days[day_of_week_num]

    return day_of_week_name


def execute_weekly_analysis(
    send_only_to_emails: Optional[List[str]] = None,
    date: Optional[str] = None,
) -> None:
    iostream = IOConsole()
    with IOStream.set_default(iostream):
        if date is None:
            date = (datetime.today().date() - timedelta(1)).isoformat()
        print("Starting weekly analysis.")
        if send_only_to_emails is not None:
            day_of_week = None
        else:
            day_of_week = _get_day_of_week(date)
        id_email_dict = json.loads(get_user_ids_and_emails(day_of_week=day_of_week))

        # if send_only_to_emails is None:
        #     send_only_to_emails = ["robert@airt.ai", "harish@airt.ai"]

        for user_id, email in id_email_dict.items():
            if send_only_to_emails is not None and email not in send_only_to_emails:
                SKIPPED_USERS_TOTAL.inc()
                print(f"Skipping user_id: {user_id} - email {email}")
                continue

            try:
                conv_id, conv_uuid = _get_conv_id_and_uuid(user_id=user_id, email=email)
            except Exception as e:
                print(
                    f"Failed to create chat for user_id: {user_id} - email {email}.\nError: {e}"
                )
                traceback.print_stack()
                traceback.print_exc()
                WEEKLY_ANALYSIS_EXCEPTIONS_TOTAL.inc()
                continue
            weekly_analysis_team = None
            try:
                login_url_response = get_login_url(
                    user_id=user_id, conv_id=conv_id
                ).get("login_url")
                if not login_url_response == ALREADY_AUTHENTICATED:
                    # Do not proceed with Google Ads analysis for non authenticated users
                    print(
                        f"Skipping user_id: {user_id} - email {email} because he hasn't logged in yet."
                    )
                    _delete_chat_webhook(user_id=user_id, conv_id=conv_id)
                    SKIPPED_USERS_TOTAL.inc()
                    continue

                # Always get the weekly report for the previous day
                weekly_reports = get_weekly_report(
                    date=date, user_id=user_id, conv_id=conv_id
                )
                if weekly_reports is None:
                    _delete_chat_webhook(user_id=user_id, conv_id=conv_id)
                    SKIPPED_USERS_TOTAL.inc()
                    continue

                (
                    weekly_report_message,
                    main_email_template,
                ) = construct_weekly_report_email_from_template(
                    weekly_reports=json.loads(weekly_reports), date=date
                )

                task = _create_task_message(date, weekly_reports, weekly_report_message)

                weekly_analysis_team = WeeklyAnalysisTeam(
                    task=task,
                    user_id=user_id,
                    conv_id=conv_id,
                )
                WEEKLY_ANALYSIS_TEAM_CONVERSATIONS_TOTAL.inc()
                weekly_analysis_team.initiate_chat()
                _validate_conversation_and_send_email(
                    weekly_analysis_team=weekly_analysis_team,
                    conv_uuid=conv_uuid,
                    email=email,
                    weekly_report_message=weekly_report_message,
                    main_email_template=main_email_template,
                )

            except Exception as e:
                WEEKLY_ANALYSIS_EXCEPTIONS_TOTAL.inc()
                print(
                    f"Weekly analysis failed for user_id: {user_id} - email {email}.\nError: {e}"
                )
                traceback.print_stack()
                traceback.print_exc()
                _delete_chat_webhook(user_id=user_id, conv_id=conv_id)
            finally:
                if weekly_analysis_team:
                    Team.pop_team(user_id=user_id, conv_id=conv_id)
        print("Weekly analysis completed.")
