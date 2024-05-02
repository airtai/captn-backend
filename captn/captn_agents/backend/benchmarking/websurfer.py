from ..tools._functions import (
    get_get_info_from_the_web_page,
    get_llm_config_gpt_3_5,
    get_llm_config_gpt_4,
)

__all__ = ["benchmark_websurfer"]


def benchmark_websurfer(
    url: str,
    outer_retries: int = 1,
    inner_retries: int = 10,
    summarizer_llm: str = "gpt3-5",
    llm: str = "gpt4",
    navigator_llm: str = "gpt4",
    timestamp: str = "2024-01-01T00:00:0",
    introduce_give_up_after: int = 7,
) -> str:
    llm_configs = {
        "gpt3-5": get_llm_config_gpt_3_5(),
        "gpt4": get_llm_config_gpt_4(),
    }

    get_info_from_the_web_page = get_get_info_from_the_web_page(
        outer_retries=outer_retries,
        inner_retries=inner_retries,
        summarizer_llm_config=llm_configs[summarizer_llm],
        websurfer_llm_config=llm_configs[llm],
        timestamp=timestamp,
        websurfer_navigator_llm_config=llm_configs[navigator_llm],
        max_retires_before_give_up_message=introduce_give_up_after,
    )
    # TODO: Fix type-ignore
    last_message = get_info_from_the_web_page(
        url=url,  # type: ignore[call-arg]
    )

    if not last_message.startswith(
        "Here is a summary of the information you requested:"
    ):
        raise AssertionError(last_message)

    return last_message
