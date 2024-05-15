from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from annotated_types import Len
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

from ....google_ads.client import check_for_client_approval, google_ads_create_update
from ..toolboxes import Toolbox
from ._functions import (
    Context,
)
from ._google_ads_team_tools import (
    add_shared_functions,
    properties_config,
)

__all__ = ("create_campaign_creation_team_toolbox",)


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
    clients_question_answer_list: List[Tuple[Dict[str, Any], Optional[str]]],
    ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
) -> Union[Dict[str, Any], str]:
    ad_group = ad_group_with_ad_and_keywords.ad_group
    ad_group.customer_id = ad_group_with_ad_and_keywords.customer_id
    ad_group.campaign_id = ad_group_with_ad_and_keywords.campaign_id

    ad_group_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        ad=ad_group,
        endpoint="/create-ad-group",
        already_checked_clients_approval=True,
    )

    return ad_group_response


def _create_ad_group_ad(
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[Dict[str, Any], Optional[str]]],
    ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
    ad_group_id: str,
) -> Union[Dict[str, Any], str]:
    ad_group_ad = ad_group_with_ad_and_keywords.ad_group_ad
    ad_group_ad.customer_id = ad_group_with_ad_and_keywords.customer_id
    ad_group_ad.ad_group_id = ad_group_id

    ad_group_ad_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        ad=ad_group_ad,
        endpoint="/create-ad-group-ad",
        already_checked_clients_approval=True,
    )
    return ad_group_ad_response


def _create_ad_group_keyword(
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[Dict[str, Any], Optional[str]]],
    ad_group_keyword: AdGroupCriterionForCreation,
    ad_group_id: str,
    customer_id: str,
) -> Union[Dict[str, Any], str]:
    ad_group_keyword.customer_id = customer_id
    ad_group_keyword.ad_group_id = ad_group_id
    keyword_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
        ad=ad_group_keyword,
        endpoint="/add-keywords-to-ad-group",
        already_checked_clients_approval=True,
    )
    return keyword_response


def _create_ad_group_keywords(
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[Dict[str, Any], Optional[str]]],
    ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
    ad_group_id: str,
) -> Union[Dict[str, Any], str]:
    response = ""
    for keyword in ad_group_with_ad_and_keywords.keywords:
        keyword_response = _create_ad_group_keyword(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answer_list=clients_question_answer_list,
            ad_group_keyword=keyword,
            ad_group_id=ad_group_id,
            customer_id=ad_group_with_ad_and_keywords.customer_id,
        )
        response += f"Keyword: {keyword_response}\n"
    return response


def create_campaign_creation_team_toolbox(
    user_id: int,
    conv_id: int,
    clients_question_answer_list: List[Tuple[Dict[str, Any], Optional[str]]],
) -> Toolbox:
    toolbox = Toolbox()

    context = Context(
        user_id=user_id,
        conv_id=conv_id,
        clients_question_answer_list=clients_question_answer_list,
    )
    toolbox.set_context(context)

    @toolbox.add_function("Create an ad group with a single ad and a list of keywords")
    def create_ad_group_with_ad_and_keywords(
        ad_group_with_ad_and_keywords: Annotated[
            AdGroupWithAdAndKeywords, "An ad group with an ad and a list of keywords"
        ],
        # the context will be injected by the toolbox
        context: Context,
    ) -> Union[Dict[str, Any], str]:
        """Create an ad group with a single ad and a list of keywords

        Args:
            ad_group_with_ad_and_keywords (AdGroupWithAdAndKeywords): The ad group with an ad and a list of keywords
            context (Context): The context. It will be injected by the toolbox and not available to the LLM proposing the code.
                It should be set up prior to calling `ìnitialize_chat` or `send_message` by calling `toolbox.set_context` function.

        Returns:
            Union[Dict[str, Any], str]: The response message
        """
        # TODO: If any of the creation fails, we should rollback the changes
        # and return the error message (delete ad_group, other resources will be deleted automatically)

        user_id = context.user_id
        conv_id = context.conv_id
        clients_question_answer_list = context.clients_question_answer_list

        modification_function_parameters = {}
        modification_function_parameters["ad_group_with_ad_and_keywords"] = (
            ad_group_with_ad_and_keywords.model_dump()
        )
        error_msg = check_for_client_approval(
            modification_function_parameters=modification_function_parameters,
            clients_question_answer_list=clients_question_answer_list,
        )
        if error_msg:
            raise ValueError(error_msg)

        ad_group_response = _create_ad_group(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answer_list=clients_question_answer_list,
            ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
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
            ad_group_id=ad_group_id,
        )
        response += f"Ad group ad: {ad_group_ad_response}\n"

        ad_group_keywords_response = _create_ad_group_keywords(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answer_list=clients_question_answer_list,
            ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
            ad_group_id=ad_group_id,
        )
        response += ad_group_keywords_response  # type: ignore

        return response

    add_shared_functions(toolbox)

    return toolbox
