from ..tools._functions import (
    get_get_info_from_the_web_page,
    llm_config_gpt_3_5,
    llm_config_gpt_4,
)

__all__ = ["benchmark_websurfer"]

DEFAULT_TASK = """We are tasked with creating a new Google Ads campaign for the website.
In order to create the campaign, we need to understand the website and its products/services.
Our task is to provide a summary of the website, including the products/services offered, target audience, and any unique selling points.
This is the first step in creating the Google Ads campaign so please gather as much information as possible.
Visit the most likely pages to be advertised, such as the homepage, product pages, and any other relevant pages.
Please provide a detailed summary of the website as JSON-encoded text as instructed in the guidelines.

AFTER visiting the home page, create a step-by-step plan BEFORE visiting the other pages.
"""

DEFAULT_TASK_GUIDELINES = "Please provide a summary of the website, including the products/services offered, target audience, and any unique selling points."

_llm_configs = {
    "gpt3-5": llm_config_gpt_3_5,
    "gpt4": llm_config_gpt_4,
}


def benchmark_websurfer(
    url: str,
    task: str = DEFAULT_TASK,
    task_guidelines: str = DEFAULT_TASK_GUIDELINES,
    outer_retries: int = 1,
    inner_retries: int = 10,
    summarizer_llm: str = "gpt3-5",
    llm: str = "gpt4",
    navigator_llm: str = "gpt4",
    timestamp: str = "2024-01-01T00:00:0",
) -> str:
    get_info_from_the_web_page = get_get_info_from_the_web_page(
        outer_retries=outer_retries,
        inner_retries=inner_retries,
        summarizer_llm_config=_llm_configs[summarizer_llm],
        websurfer_llm_config=_llm_configs[llm],
        timestamp=timestamp,
        websurfer_navigator_llm_config=_llm_configs[navigator_llm],
    )
    last_message = get_info_from_the_web_page(
        url=url,
        task=task,
        task_guidelines=task_guidelines,
    )

    if not last_message.startswith(
        "Here is a summary of the information you requested:"
    ):
        raise AssertionError(last_message)

    return last_message
