from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from annotated_types import Len
from pydantic import BaseModel, Field, field_validator
from typing_extensions import Annotated

from google_ads.model import RemoveResource, check_max_string_length_for_each_item

from ....google_ads.client import check_for_client_approval, google_ads_create_update
from ..toolboxes import Toolbox
from ._functions import (
    Context,
)
from ._google_ads_team_tools import (
    add_shared_functions,
    get_resource_id_from_response,
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
        List[
            Annotated[
                str,
                "Maximum 30 characters. If keyword insertion is used, '{KeyWord' and '}' are NOT included in the 30 characters.",
            ]
        ],
        Len(min_length=15, max_length=15),
    ]
    descriptions: Annotated[
        List[
            Annotated[
                str,
                "Maximum 90 characters. If keyword insertion is used, '{KeyWord' and '}' are NOT included in the 90 characters.",
            ]
        ],
        Len(min_length=4, max_length=4),
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

    @classmethod
    def validate_field(
        cls,
        field_name: str,
        field: List[str],
        max_string_length: int,
    ) -> Optional[List[str]]:
        error_message = check_max_string_length_for_each_item(
            field_name=field_name, field=field, max_string_length=max_string_length
        )

        if error_message:
            raise ValueError(error_message)
        return field

    @field_validator("headlines")
    def headlines_validator(cls, headlines: List[str]) -> Optional[List[str]]:
        return cls.validate_field(
            field_name="headlines",
            field=headlines,
            max_string_length=30,
        )

    @field_validator("descriptions")
    def descriptions_validator(cls, descriptions: List[str]) -> Optional[List[str]]:
        return cls.validate_field(
            field_name="descriptions",
            field=descriptions,
            max_string_length=90,
        )


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


def _create_ad_group(
    user_id: int,
    conv_id: int,
    recommended_modifications_and_answer_list: List[
        Tuple[Dict[str, Any], Optional[str]]
    ],
    ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
    login_customer_id: Optional[str] = None,
) -> Union[Dict[str, Any], str]:
    ad_group = ad_group_with_ad_and_keywords.ad_group
    ad_group.customer_id = ad_group_with_ad_and_keywords.customer_id
    ad_group.campaign_id = ad_group_with_ad_and_keywords.campaign_id

    ad_group_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
        ad=ad_group,
        endpoint="/create-ad-group",
        login_customer_id=login_customer_id,
        already_checked_clients_approval=True,
    )

    return ad_group_response


def _create_ad_group_ad(
    user_id: int,
    conv_id: int,
    recommended_modifications_and_answer_list: List[
        Tuple[Dict[str, Any], Optional[str]]
    ],
    ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
    ad_group_id: str,
    login_customer_id: Optional[str] = None,
) -> Union[Dict[str, Any], str]:
    ad_group_ad = ad_group_with_ad_and_keywords.ad_group_ad
    ad_group_ad.customer_id = ad_group_with_ad_and_keywords.customer_id
    ad_group_ad.ad_group_id = ad_group_id

    ad_group_ad_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
        ad=ad_group_ad,
        endpoint="/create-ad-group-ad",
        login_customer_id=login_customer_id,
        already_checked_clients_approval=True,
    )
    return ad_group_ad_response


def _create_ad_group_keyword(
    user_id: int,
    conv_id: int,
    recommended_modifications_and_answer_list: List[
        Tuple[Dict[str, Any], Optional[str]]
    ],
    ad_group_keyword: AdGroupCriterionForCreation,
    ad_group_id: str,
    customer_id: str,
    login_customer_id: Optional[str] = None,
) -> Union[Dict[str, Any], str]:
    ad_group_keyword.customer_id = customer_id
    ad_group_keyword.ad_group_id = ad_group_id
    keyword_response = google_ads_create_update(
        user_id=user_id,
        conv_id=conv_id,
        recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
        ad=ad_group_keyword,
        endpoint="/add-keywords-to-ad-group",
        login_customer_id=login_customer_id,
        already_checked_clients_approval=True,
    )
    return keyword_response


def _create_ad_group_keywords(
    user_id: int,
    conv_id: int,
    recommended_modifications_and_answer_list: List[
        Tuple[Dict[str, Any], Optional[str]]
    ],
    ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
    ad_group_id: str,
    list_of_resources: List[RemoveResource],
    login_customer_id: Optional[str] = None,
) -> Union[Dict[str, Any], str]:
    response = ""
    for keyword in ad_group_with_ad_and_keywords.keywords:
        keyword_response = _create_ad_group_keyword(
            user_id=user_id,
            conv_id=conv_id,
            recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
            ad_group_keyword=keyword,
            ad_group_id=ad_group_id,
            customer_id=ad_group_with_ad_and_keywords.customer_id,
            login_customer_id=login_customer_id,
        )
        keyword_id = get_resource_id_from_response(keyword_response)  # type: ignore[arg-type]
        list_of_resources.append(
            RemoveResource(
                customer_id=ad_group_with_ad_and_keywords.customer_id,
                parent_id=ad_group_id,
                resource_id=keyword_id,
                resource_type="ad_group_criterion",
            )
        )
        response += f"Keyword '{keyword.keyword_text}': {keyword_response}\n"
    return response


def _remove_resources(
    user_id: int,
    conv_id: int,
    list_of_resources: List[RemoveResource],
    login_customer_id: Optional[str] = None,
) -> None:
    for remove_resource in list_of_resources[::-1]:
        remove_response = google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            recommended_modifications_and_answer_list=[],
            ad=remove_resource,
            endpoint="/remove-google-ads-resource",
            login_customer_id=login_customer_id,
            already_checked_clients_approval=True,
        )
        print(remove_response)
    print("Resources removed successfully")


def _create_ad_group_with_ad_and_keywords(
    ad_group_with_ad_and_keywords: Annotated[
        AdGroupWithAdAndKeywords, "An ad group with an ad and a list of keywords"
    ],
    context: Context,
    login_customer_id: Optional[str] = None,
) -> Union[Dict[str, Any], str]:
    list_of_resources = []
    try:
        ad_group_response = _create_ad_group(
            user_id=context.user_id,
            conv_id=context.conv_id,
            recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
            ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
            login_customer_id=login_customer_id,
        )
        if isinstance(ad_group_response, dict):
            return ad_group_response
        response = f"Ad group '{ad_group_with_ad_and_keywords.ad_group.name}': {ad_group_response}\n"
        ad_group_id = get_resource_id_from_response(ad_group_response)
        list_of_resources.append(
            RemoveResource(
                customer_id=ad_group_with_ad_and_keywords.customer_id,
                resource_id=ad_group_id,
                resource_type="ad_group",
            )
        )

        ad_group_ad_response = _create_ad_group_ad(
            user_id=context.user_id,
            conv_id=context.conv_id,
            recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
            ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
            ad_group_id=ad_group_id,
            login_customer_id=login_customer_id,
        )
        ad_group_ad_id = get_resource_id_from_response(ad_group_ad_response)  # type: ignore[arg-type]
        list_of_resources.append(
            RemoveResource(
                customer_id=ad_group_with_ad_and_keywords.customer_id,
                parent_id=ad_group_id,
                resource_id=ad_group_ad_id,
                resource_type="ad",
            )
        )

        response += f"Ad group ad with final url - '{ad_group_with_ad_and_keywords.ad_group_ad.final_url}': {ad_group_ad_response}\n"

        ad_group_keywords_response = _create_ad_group_keywords(
            user_id=context.user_id,
            conv_id=context.conv_id,
            recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
            ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
            ad_group_id=ad_group_id,
            list_of_resources=list_of_resources,
            login_customer_id=login_customer_id,
        )
        response += ad_group_keywords_response  # type: ignore
        context.changes_made += f"\n{response}"
    except Exception as e:
        _remove_resources(
            user_id=context.user_id,
            conv_id=context.conv_id,
            list_of_resources=list_of_resources,
            login_customer_id=login_customer_id,
        )
        raise e

    return response


def create_campaign_creation_team_toolbox(
    user_id: int,
    conv_id: int,
    recommended_modifications_and_answer_list: List[
        Tuple[Dict[str, Any], Optional[str]]
    ],
) -> Toolbox:
    toolbox = Toolbox()

    context = Context(
        user_id=user_id,
        conv_id=conv_id,
        recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
        toolbox=toolbox,
    )
    toolbox.set_context(context)

    @toolbox.add_function("""Create an ad group with a single ad and a list of keywords. Make sure you use the correct customer_id and campaign_id.
You can find the customer_id by using 'list_accessible_customers' function and the campaign_id will be provided to you after you create a campaign.""")
    def create_ad_group_with_ad_and_keywords(
        ad_group_with_ad_and_keywords: Annotated[
            AdGroupWithAdAndKeywords,
            "An ad group with an ad (15 headlines and 4 descriptions) and a list of keywords",
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
        modification_function_parameters = {}
        modification_function_parameters["ad_group_with_ad_and_keywords"] = (
            ad_group_with_ad_and_keywords.model_dump()
        )
        error_msg = check_for_client_approval(
            modification_function_parameters=modification_function_parameters,
            recommended_modifications_and_answer_list=context.recommended_modifications_and_answer_list,
        )
        if error_msg:
            raise ValueError(error_msg)

        return _create_ad_group_with_ad_and_keywords(
            ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
            context=context,
        )

    add_shared_functions(toolbox)

    return toolbox
