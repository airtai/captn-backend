import os
import random
import sys
import time
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator

import pandas as pd
import typer
from filelock import FileLock

# TODO: How to import the helper_test_get_info_from_the_web_page function from the test_functions.py file?
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from ci.captn.captn_agents.backend.tools.test_functions import (  # noqa: E402
    TestWebSurfer,
)


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
    timestamp: str = "2024-01-01T00:00:0",
) -> Dict[str, Any]:
    time_start = time.time()
    success = False
    last_message = ""
    try:
        last_message = TestWebSurfer.helper_test_get_info_from_the_web_page(
            url=url,
            outer_retries=outer_retries,
            inner_retries=inner_retries,
            summarizer_llm=summarizer_llm,
            websurfer_llm=websurfer_llm,
            websurfer_navigator_llm=websurfer_navigator_llm,
            timestamp=timestamp,
        )
        assert last_message.startswith(
            "Here is a summary of the information you requested:"
        )
        success = True
    except Exception as e:
        print(e)
    finally:
        total_time = time.time() - time_start
        result = {
            "url": url,
            "time": total_time,
            "success": success,
            "summarizer_llm": summarizer_llm,
            "websurfer_llm": websurfer_llm,
            "websurfer_navigator_llm": websurfer_navigator_llm,
            "inner_retries": inner_retries,
            "last_message": last_message,
            "status": "DONE",
            "timestamp": timestamp,
        }

    return result


REPORTS_FOLDER = Path(__file__).resolve().parent / "reports"
REPORTS_FOLDER.mkdir(exist_ok=True)

app = typer.Typer()


def _get_file_name(file_suffix: str) -> str:
    file_name = f"get_info_from_the_web_page_{file_suffix}.csv"
    return file_name


def create_ag_report(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["success"])
    group = df.groupby("url")["success"]
    total = group.count()
    success = group.sum()
    success_rate = (success / total).rename("success_rate")

    group = df.groupby("url")["time"]
    avg_time = group.mean().rename("avg_time")

    return pd.concat([success_rate, avg_time], axis=1).sort_values(
        "success_rate", ascending=True
    )


@contextmanager
def lock_file(file_suffix: str) -> Iterator[Path]:
    file_name_all_tests = _get_file_name(file_suffix)
    report_all_runs_path = REPORTS_FOLDER / file_name_all_tests
    report_all_runs_path_lock = REPORTS_FOLDER / f"{file_name_all_tests}.lock"

    with FileLock(str(report_all_runs_path_lock)):
        yield report_all_runs_path
    report_all_runs_path_lock.unlink()


@app.command()
def generate_aggregated_report(
    file_suffix: str = typer.Option(
        "test",
        "--file-suffix",
        "-fs",
        help="File suffix for the aggregated report",
    ),
):
    with lock_file(file_suffix) as report_all_runs_path:
        df = pd.read_csv(report_all_runs_path)
        report_df = create_ag_report(df)

        report_aggregated_path = (
            REPORTS_FOLDER / f"get_info_from_the_web_page_aggregated_{file_suffix}.csv"
        )
        report_df.to_csv(report_aggregated_path)


def generate_reports(result: Dict[str, Any], file_suffix: str):
    with lock_file(file_suffix) as report_all_runs_path:
        df = pd.read_csv(report_all_runs_path)
        # Delete the row with the same id
        df = df[df["timestamp"] != result["timestamp"]]
        # Add the updated row
        df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)

        df.to_csv(report_all_runs_path, index=False)


@app.command()
def generate_task_table(
    file_suffix: str = typer.Option(
        "test",
        help="File suffix for the reports",
    ),
    repeat: int = typer.Option(
        10,
        help="Number of times to repeat each url",
    ),
):
    df = pd.DataFrame(
        columns=[
            "timestamp",
            "url",
            "time",
            "success",
            "summarizer_llm",
            "websurfer_llm",
            "websurfer_navigator_llm",
            "inner_retries",
            "last_message",
            "status",
        ]
    )

    URLS = [
        "https://www.ikea.com/gb/en/",
        "https://www.disneystore.eu",
        "https://www.hamleys.com/",
        "https://www.konzum.hr",
        "https://faststream.airt.ai",
    ]
    URLS = URLS * repeat

    df["url"] = URLS
    timestamp = "2024-01-01T00:00:0"
    timestamps = [timestamp + str(i) for i in range(len(URLS))]
    df["timestamp"] = timestamps

    file_name = _get_file_name(file_suffix)
    report_all_runs_path = REPORTS_FOLDER / file_name
    df.to_csv(report_all_runs_path, index=False)


@app.command()
def run_tests(
    inner_retries: int = typer.Option(
        10,
        help="Number of retries to fix the created summary",
    ),
    summarizer_llm: Models = typer.Option(  # noqa: B008
        Models.gpt3_5,
        help="Model which will be used by the web surfer summarizer",
    ),
    websurfer_llm: Models = typer.Option(  # noqa: B008
        Models.gpt4,
        help="Model which will be used by the web surfer",
    ),
    websurfer_navigator_llm: Models = typer.Option(  # noqa: B008
        Models.gpt4,
        help="Model which will be used by the web surfer navigator",
    ),
    file_suffix: str = typer.Option(
        "test",
        help="File suffix for the reports",
    ),
):
    outer_retries: int = 1
    while True:
        row: pd.Series
        with lock_file(file_suffix) as report_all_runs_path:
            if not report_all_runs_path.exists():
                print("Generating task table")
                generate_task_table(file_suffix=file_suffix)

            df = pd.read_csv(report_all_runs_path)

            df_isnan = df["status"].isna()
            if not df_isnan.any():
                print("All tasks are done")
                break

            df_status_nan = df[df_isnan]
            count = df_status_nan.shape[0]
            i = random.randint(0, count - 1)
            row = df_status_nan.iloc[i]

            df["status"] = df["status"].astype(str)
            df.loc[df["timestamp"] == row["timestamp"], "status"] = "PENDING"

            df.to_csv(report_all_runs_path, index=False)

        result = run_test(
            url=row["url"],
            outer_retries=outer_retries,
            inner_retries=inner_retries,
            summarizer_llm=summarizer_llm,
            websurfer_llm=websurfer_llm,
            websurfer_navigator_llm=websurfer_navigator_llm,
            timestamp=row["timestamp"],
        )
        generate_reports(result=result, file_suffix=file_suffix)

        generate_aggregated_report(file_suffix=file_suffix)


if __name__ == "__main__":
    app()
