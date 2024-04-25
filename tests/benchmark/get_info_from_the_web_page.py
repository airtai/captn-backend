import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import typer
from filelock import FileLock

from captn.captn_agents.backend.tools._functions import (
    get_get_info_from_the_web_page,
    llm_config_gpt_3_5,
    llm_config_gpt_4,
)

LLM_CONFIGS = {
    "gpt3-5": llm_config_gpt_3_5,
    "gpt4": llm_config_gpt_4,
}


class Models(str, Enum):
    gpt3_5 = "gpt3-5"
    gpt4 = "gpt4"


def run_test(
    url: str,
    outer_retries: int,
    inner_retries: int,
    summarizer_llm: str,
    websurfer_llm: str,
    websurfer_navigator_llm: str,
) -> Dict[str, Any]:
    time_start = time.time()
    success = False
    last_message = ""
    try:
        # raise Exception("Test exception")
        last_message = get_get_info_from_the_web_page(
            outer_retries=outer_retries,
            inner_retries=inner_retries,
            summarizer_llm_config=LLM_CONFIGS[summarizer_llm],
            websurfer_llm_config=LLM_CONFIGS[websurfer_llm],
            websurfer_navigator_llm_config=LLM_CONFIGS[websurfer_navigator_llm],
        )(
            url=url,
            # task="I need website summary which will help me create Google Ads ad groups, ads, and keywords for the website.",
            task="""We are tasked with creating a new Google Ads campaign for the website.
In order to create the campaign, we need to understand the website and its products/services.
Our task is to provide a summary of the website, including the products/services offered, target audience, and any unique selling points.
This is the first step in creating the Google Ads campaign so please gather as much information as possible.
Visit the most likely pages to be advertised, such as the homepage, product pages, and any other relevant pages.
Please provide a detailed summary of the website as JSON-encoded text as instructed in the guidelines.

AFTER visiting the home page, create a step-by-step plan BEFORE visiting the other pages.
""",
            task_guidelines="Please provide a summary of the website, including the products/services offered, target audience, and any unique selling points.",
        )

        assert "SUMMARY" in last_message
        success = True
    except Exception as e:
        print(f"Error handling.... {last_message}")
        print(e)
    finally:
        total_time = time.time() - time_start
        result = {
            "name": "get_info_from_the_web_page",
            "time": total_time,
            "success": success,
            "summarizer_llm": summarizer_llm,
            "websurfer_llm": websurfer_llm,
            "websurfer_navigator_llm": websurfer_navigator_llm,
            "outer_retries": outer_retries,
            "inner_retries": inner_retries,
            "last_message": last_message,
        }

    return result


REPORTS_FOLDER = Path(__file__).resolve().parent / "reports"
REPORTS_FOLDER.mkdir(exist_ok=True)

app = typer.Typer()


def _get_file_name(file_suffix: str) -> str:
    file_name = f"get_info_from_the_web_page_{file_suffix}.csv"
    return file_name


@app.command()
def generate_aggregated_report(
    file_suffix: str = typer.Option(
        "test",
        "--file-suffix",
        "-fs",
        help="File suffix for the aggregated report",
    ),
):
    file_name_all_tests = _get_file_name(file_suffix)
    report_all_runs_path = REPORTS_FOLDER / file_name_all_tests
    df = pd.read_csv(report_all_runs_path, sep="\t")

    success_df = df["success"].value_counts(normalize=True)

    report = df[
        [
            "name",
            "summarizer_llm",
            "websurfer_llm",
            "websurfer_navigator_llm",
            "success",
        ]
    ].drop_duplicates()

    time_average = (
        df[["success", "time"]]
        .groupby(
            [
                "success",
            ]
        )
        .mean()
    )

    report = report.join(time_average, on="success", how="outer")
    report = report.join(success_df, on="success", how="outer")
    report = report.rename(columns={"proportion": "percentage"})
    print(report)

    report_aggregated_path = (
        REPORTS_FOLDER / f"get_info_from_the_web_page_aggregated_{file_suffix}.csv"
    )
    report.to_csv(str(report_aggregated_path), sep="\t")


def generate_reports(results: Dict[str, Any], file_suffix: str):
    df = pd.DataFrame(
        data=results,
        columns=[
            "name",
            "summarizer_llm",
            "websurfer_llm",
            "websurfer_navigator_llm",
            "time",
            "success",
            "outer_retries",
            "inner_retries",
            "last_message",
        ],
    )

    file_name = _get_file_name(file_suffix)
    report_all_runs_path = REPORTS_FOLDER / file_name
    report_all_runs_path_lock = REPORTS_FOLDER / f"{file_name}.lock"

    with FileLock(str(report_all_runs_path_lock)):
        # work with the file as it is now locked
        header = not report_all_runs_path.exists()
        df.to_csv(
            str(report_all_runs_path), mode="a", header=header, sep="\t", index=False
        )
    report_all_runs_path_lock.unlink()


@app.command()
def run_tests(
    outer_retries: int = typer.Option(
        1,
        "--outer-retries",
        "-or",
        help="Number of complete retries",
    ),
    inner_retries: int = typer.Option(
        10,
        "--inner-retries",
        "-ir",
        help="Number of retries to fix the created summary",
    ),
    summarizer_llm: Models = typer.Option(  # noqa: B008
        Models.gpt3_5,
        "--summarizer-llm",
        "-sllm",
        help="Model which will be used by the web surfer summarizer",
    ),
    websurfer_llm: Models = typer.Option(  # noqa: B008
        Models.gpt4,
        "--websurfer-llm",
        "-wsllm",
        help="Model which will be used by the web surfer",
    ),
    websurfer_navigator_llm: Models = typer.Option(  # noqa: B008
        Models.gpt3_5,
        "--websurfer-navgator-llm",
        "-wsnllm",
        help="Model which will be used by the web surfer navigator",
    ),
    file_suffix: str = typer.Option(
        "test",
        "--file-suffix",
        "-fs",
        help="File suffix for the reports",
    ),
):
    URLS = ["https://www.ikea.com/gb/en/"]
    results = []
    for url in URLS:
        result = run_test(
            url=url,
            outer_retries=outer_retries,
            inner_retries=inner_retries,
            summarizer_llm=summarizer_llm,
            websurfer_llm=websurfer_llm,
            websurfer_navigator_llm=websurfer_navigator_llm,
        )
        results.append(result)

    generate_reports(results=results, file_suffix=file_suffix)


if __name__ == "__main__":
    app()
