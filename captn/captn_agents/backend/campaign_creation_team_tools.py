from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union

from annotated_types import Len
from autogen.agentchat import AssistantAgent, ConversableAgent
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

from captn.google_ads.client import google_ads_create_update

from .function_configs import properties_config

__all__ = ("add_create_ad_group_with_ad_and_keywords_to_agent",)


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


class AdGroupAdForCreation(AdBase):
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


class AdGroupCriterionForCreation(AdBase):
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


class AdGroupForCreation(AdBase):
    campaign_id: Annotated[
        Optional[str],
        Field(..., description=properties_config["campaign_id"]["description"]),
    ] = None
    name: Annotated[str, Field(..., description="The name of the Ad Group")]
    # budget for the ad group isn't needed for creation
    # cpc_bid_micros: Annotated[
    #     Optional[int], properties_config["cpc_bid_micros"]["description"]
    # ] = None


class AdGroupWithAdAndKeywords(BaseModel):
    customer_id: Annotated[
        str, Field(..., description=properties_config["customer_id"]["description"])
    ]
    campaign_id: Annotated[
        str, Field(..., description=properties_config["campaign_id"]["description"])
    ]
    ad_group: Annotated[AdGroupForCreation, "The ad group to be created"]
    ad_group_ad: Annotated[
        AdGroupAdForCreation, "The ad for the ad group which will be created"
    ]
    keywords: Annotated[List[AdGroupCriterionForCreation], Len(min_length=1)]


def _get_resource_id_from_response(response: str) -> str:
    return response.split("/")[-1].replace(".", "")


def _create_ad_group(
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[str, Optional[str]]],
    ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
    clients_approval_message: str,
    modification_question: str,
) -> Union[Dict[str, Any], str]:
    ad_group = ad_group_with_ad_and_keywords.ad_group
    ad_group.customer_id = ad_group_with_ad_and_keywords.customer_id
    ad_group.campaign_id = ad_group_with_ad_and_keywords.campaign_id

    ad_group_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=ad_group,
        endpoint="/create-ad-group",
        skip_fields_check=True,
    )

    return ad_group_response


def _create_ad_group_ad(
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[str, Optional[str]]],
    ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
    clients_approval_message: str,
    modification_question: str,
    ad_group_id: str,
) -> Union[Dict[str, Any], str]:
    ad_group_ad = ad_group_with_ad_and_keywords.ad_group_ad
    ad_group_ad.customer_id = ad_group_with_ad_and_keywords.customer_id
    ad_group_ad.ad_group_id = ad_group_id

    ad_group_ad_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=ad_group_ad,
        endpoint="/create-ad-group-ad",
        skip_fields_check=True,
    )
    return ad_group_ad_response


def _create_ad_group_keyword(
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[str, Optional[str]]],
    ad_group_keyword: AdGroupCriterionForCreation,
    clients_approval_message: str,
    modification_question: str,
    ad_group_id: str,
    customer_id: str,
) -> Union[Dict[str, Any], str]:
    ad_group_keyword.customer_id = customer_id
    ad_group_keyword.ad_group_id = ad_group_id
    keyword_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad=ad_group_keyword,
        endpoint="/add-keywords-to-ad-group",
        skip_fields_check=True,
    )
    return keyword_response


def _create_ad_group_keywords(
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[str, Optional[str]]],
    ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
    clients_approval_message: str,
    modification_question: str,
    ad_group_id: str,
) -> Union[Dict[str, Any], str]:
    response = ""
    for keyword in ad_group_with_ad_and_keywords.keywords:
        keyword_response = _create_ad_group_keyword(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answer_list=clients_question_answer_list,
            ad_group_keyword=keyword,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad_group_id=ad_group_id,
            customer_id=ad_group_with_ad_and_keywords.customer_id,
        )
        response += f"Keyword: {keyword_response}\n"  # type: ignore
    return response


def create_ad_group_with_ad_and_keywords(
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[str, Optional[str]]],
    ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
    clients_approval_message: str,
    modification_question: str,
) -> Union[Dict[str, Any], str]:
    # TODO: If any of the creation fails, we should rollback the changes
    # and return the error message (delete ad_group, other resources will be deleted automatically)
    ad_group_response = _create_ad_group(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
    )
    if isinstance(ad_group_response, dict):
        return ad_group_response
    response = f"Ad group: {ad_group_response}\n"
    ad_group_id = _get_resource_id_from_response(ad_group_response)

    ad_group_ad_response = _create_ad_group_ad(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad_group_id=ad_group_id,
    )
    response += f"Ad group ad: {ad_group_ad_response}\n"

    ad_group_keywords_response = _create_ad_group_keywords(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
        clients_approval_message=clients_approval_message,
        modification_question=modification_question,
        ad_group_id=ad_group_id,
    )
    response += ad_group_keywords_response  # type: ignore

    return response


def add_create_ad_group_with_ad_and_keywords_to_agent(
    *,
    agent: AssistantAgent,
    executor: Optional[ConversableAgent] = None,
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[str, Optional[str]]],
) -> Callable[..., str]:
    """Add create_ad_group_with_ad_and_keywords to the agent

    Args:
        agent (AssistantAgent): The agent to add the function to
        executor (Optional[ConversableAgent], optional): The executor of the function, typicall UserProxyAgent.
            If None, agent will be used as executor as well. Defaults to None.
        user_id (int): The user id
        conv_id (int): The conversation id
        clients_question_answer_list (List[Tuple[str, Optional[str]]]): The list of questions and answers

    Returns:
        Callable[..., str]: The create_ad_group_with_ad_and_keywords function
    """
    if executor is None:
        executor = agent

    clients_approval_message_desc = properties_config["clients_approval_message"][
        "description"
    ]

    modification_question_desc = properties_config["modification_question"][
        "description"
    ]

    @executor.register_for_execution()  # type: ignore[misc]
    @agent.register_for_llm(  # type: ignore[misc]
        name="create_ad_group_with_ad_and_keywords",
        description="Create an ad group with a single ad and a list of keywords",
    )
    def _create_ad_group_with_ad_and_keywords(
        ad_group_with_ad_and_keywords: Annotated[
            AdGroupWithAdAndKeywords, "An ad group with an ad and a list of keywords"
        ],
        clients_approval_message: Annotated[str, clients_approval_message_desc],
        modification_question: Annotated[str, modification_question_desc],
    ) -> Union[Dict[str, Any], str]:
        return create_ad_group_with_ad_and_keywords(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answer_list=clients_question_answer_list,
            ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
        )

    return _create_ad_group_with_ad_and_keywords  # type: ignore
