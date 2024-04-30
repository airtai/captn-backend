from ..tools._functions import (
    get_get_info_from_the_web_page,
    llm_config_gpt_3_5,
    llm_config_gpt_4,
)

__all__ = ["benchmark_websurfer"]


_llm_configs = {
    "gpt3-5": llm_config_gpt_3_5,
    "gpt4": llm_config_gpt_4,
}


def benchmark_websurfer(
    url: str,
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
    )

    if not last_message.startswith(
        "Here is a summary of the information you requested:"
    ):
        raise AssertionError(last_message)

    return last_message
