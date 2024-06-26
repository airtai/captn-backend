#! /usr/bin/env python

import datetime
import itertools
import os
import random
import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List

import pandas as pd
import typer
from filelock import FileLock
from tabulate import tabulate

from ..teams._brief_creation_team import BriefCreationTeam
from .brief_creation_team import URL_SUMMARY_DICT
from .campaign_creation_team import URL_TASK_DICT
from .models import Models

app = typer.Typer()


@contextmanager
def lock_file(path: Path) -> Iterator[None]:
    lock_path = path.parents[0] / f"{path.name}.lock"

    try:
        with FileLock(str(lock_path)):
            yield
    finally:
        lock_path.unlink()


COMMON_COLUMNS = ["execution_time", "status", "success", "output", "retries"]


def _add_common_columns_and_save(
    df: pd.DataFrame, output_dir: str, file_name: str
) -> None:
    for c in COMMON_COLUMNS:
        df[c] = None

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    report_all_runs_path = output_path / file_name
    df.to_csv(report_all_runs_path, index=True)
    print(f"Task list saved to {report_all_runs_path.resolve()}")
    print(tabulate(df.iloc[:, 1:-4], headers="keys", tablefmt="simple"))


def _create_timestamps(
    repeat: int,
) -> List[datetime.datetime]:
    return [
        datetime.datetime.fromisocalendar(year=2024, week=1, day=1)
        + datetime.timedelta(seconds=i)
        for i in range(repeat)
    ]


def _create_task_df(params_list: List[Any], params_names: List[str]) -> pd.DataFrame:
    data = list(itertools.product(*params_list))
    df = pd.DataFrame(data=data, columns=params_names)
    return df


@app.command()
def generate_task_table_for_websurfer(
    inner_retries: int = typer.Option(
        10,
        help="Number of retries to fix the created summary",
    ),
    summarizer_llm: Models = typer.Option(  # noqa: B008
        Models.gpt3_5,
        help="Model which will be used by the web surfer summarizer",
    ),
    llm: Models = typer.Option(  # noqa: B008
        Models.gpt4,
        help="Model which will be used by the web surfer",
    ),
    navigator_llm: Models = typer.Option(  # noqa: B008
        Models.gpt4o,
        help="Model which will be used by the web surfer navigator",
    ),
    file_name: str = typer.Option(
        "websurfer-benchmark-tasks.csv",
        help="File name of the task list",
    ),
    repeat: int = typer.Option(
        5,
        help="Number of times to repeat each url",
    ),
    introduce_give_up_after: int = typer.Option(
        7,
        help="Number of retries before telling the LLM it is able to give up",
    ),
    output_dir: str = typer.Option(  # noqa: B008
        "./",
        help="Output directory for the reports",
    ),
) -> None:
    URLS = list(URL_SUMMARY_DICT.keys())
    timestamps = _create_timestamps(repeat=repeat)
    params_list = [
        timestamps,
        ["websurfer"],
        URLS,
        [inner_retries],
        [introduce_give_up_after],
        [summarizer_llm],
        [llm],
        [navigator_llm],
    ]
    params_names = [
        "timestamp",
        "task",
        "url",
        "inner_retries",
        "introduce_give_up_after",
        "summarizer_llm",
        "llm",
        "navigator_llm",
    ]

    df = _create_task_df(params_list=params_list, params_names=params_names)
    _add_common_columns_and_save(df, output_dir=output_dir, file_name=file_name)


@app.command()
def generate_task_table_for_brief_creation(
    llm: Models = typer.Option(  # noqa: B008
        Models.gpt4o,
        help="Model which will be used by all agents",
    ),
    file_name: str = typer.Option(
        "brief-creation-benchmark-tasks.csv",
        help="File name of the task list",
    ),
    repeat: int = typer.Option(
        5,
        help="Number of times to repeat each url",
    ),
    output_dir: str = typer.Option(  # noqa: B008
        "./",
        help="Output directory for the reports",
    ),
) -> None:
    URLS = list(URL_SUMMARY_DICT.keys())

    team_names = (
        BriefCreationTeam.get_avaliable_team_names_and_their_descriptions().keys()
    )

    params_list = [
        ["brief_creation"],
        team_names,
        URLS * repeat,
        [llm],
    ]
    params_names = [
        "task",
        "team_name",
        "url",
        "llm",
    ]

    df = _create_task_df(params_list=params_list, params_names=params_names)
    _add_common_columns_and_save(df, output_dir=output_dir, file_name=file_name)


@app.command()
def generate_task_table_for_campaign_creation(
    llm: Models = typer.Option(  # noqa: B008
        Models.gpt4o,
        help="Model which will be used by all agents",
    ),
    file_name: str = typer.Option(
        "campaign-creation-benchmark-tasks.csv",
        help="File name of the task list",
    ),
    repeat: int = typer.Option(
        5,
        help="Number of times to repeat each url",
    ),
    output_dir: str = typer.Option(  # noqa: B008
        "./",
        help="Output directory for the reports",
    ),
    end2end: bool = typer.Option(
        False,
        help="If true, generate tasks for end2end benchmarking, otherwise generate tasks for campaign creation",
    ),
) -> None:
    URLS = list(URL_TASK_DICT.keys())

    task = "end2end" if end2end else "campaign_creation"

    params_list = [
        [task],
        URLS * repeat,
        [llm],
    ]
    params_names = [
        "task",
        "url",
        "llm",
    ]

    df = _create_task_df(params_list=params_list, params_names=params_names)
    _add_common_columns_and_save(df, output_dir=output_dir, file_name=file_name)


@app.command()
def generate_task_table_for_weekly_analysis(
    llm: Models = typer.Option(  # noqa: B008
        Models.gpt4o,
        help="Model which will be used by all agents",
    ),
    file_name: str = typer.Option(
        "weekly-analysis-benchmark-tasks.csv",
        help="File name of the task list",
    ),
    repeat: int = typer.Option(
        10,
        help="Number of times to repeat each url",
    ),
    output_dir: str = typer.Option(  # noqa: B008
        "./",
        help="Output directory for the reports",
    ),
) -> None:
    URLS = ["faststream-web-search"] * repeat
    params_list = [
        ["weekly_analysis"],
        URLS,
        [llm],
    ]
    params_names = [
        "task",
        "url",
        "llm",
    ]

    df = _create_task_df(params_list=params_list, params_names=params_names)
    _add_common_columns_and_save(df, output_dir=output_dir, file_name=file_name)


def run_test(
    benchmark: Callable[..., Any],
    **kwargs: Any,
) -> Dict[str, Any]:
    try:
        time_start = time.time()
        output, retry_from_scratch_counters = benchmark(**kwargs)
        if retry_from_scratch_counters == 0:
            success = "Success"
        else:
            success = "Success with retry"
    except Exception as e:
        traceback.print_stack()
        traceback.print_exc()
        output = str(e)
        success = "Failed"
        retry_from_scratch_counters = -1
    finally:
        total_time = time.time() - time_start
        status = "DONE"

    return {
        "execution_time": total_time,
        "status": status,
        "success": success,
        "output": output,
        "retries": retry_from_scratch_counters,
    }


def get_random_nan_index(xs: pd.Series) -> Any:
    xs_isnan = xs[xs.isna()]
    count = xs_isnan.shape[0]
    if count == 0:
        return None

    i = random.randint(0, count - 1)  # nosec[B311]
    return xs_isnan.index[i]


def create_ag_report(df: pd.DataFrame, groupby_list: List[str]) -> pd.DataFrame:
    df = df.dropna(subset=["success"])
    result = (
        df.groupby(groupby_list)
        .agg(
            success_percentage=(
                "success",
                lambda x: sum(x == "Success") / len(x) * 100,
            ),
            success_with_retry_percentage=(
                "success",
                lambda x: sum(x == "Success with retry") / len(x) * 100,
            ),
            failed_percentage=("success", lambda x: sum(x == "Failed") / len(x) * 100),
            avg_time=("execution_time", "mean"),
        )
        .reset_index()
    )

    total_success_percentage = df["success"].eq("Success").mean() * 100
    total_success_with_retry_percentage = (
        df["success"].eq("Success with retry").mean() * 100
    )
    total_failed_percentage = df["success"].eq("Failed").mean() * 100
    total_avg_execution_time = df["execution_time"].mean()
    total_row = {
        "success_percentage": total_success_percentage,
        "success_with_retry_percentage": total_success_with_retry_percentage,
        "failed_percentage": total_failed_percentage,
        "avg_time": total_avg_execution_time,
    }
    for col in groupby_list:
        total_row[col] = None
    result.loc["Total"] = total_row

    result.loc[result.index[-1], "url"] = "Total"

    return result.reset_index(drop=True).round(2)


GROUP_BY_DICT = {
    "websurfer": ["url"],
    "brief_creation": ["url", "team_name"],
    "campaign_creation": ["url"],
    "end2end": ["url"],
    "weekly_analysis": ["url"],
}


@app.command()
def run_tests(
    file_path: str = typer.Option(
        ...,
        help="Path to the file with the tasks",
    ),
) -> None:
    if "BENCHMARKING_AZURE_API_ENDPOINT" in os.environ:
        os.environ["AZURE_API_ENDPOINT"] = os.environ["BENCHMARKING_AZURE_API_ENDPOINT"]
    if "BENCHMARKING_AZURE_API_KEY" in os.environ:
        os.environ["AZURE_OPENAI_API_KEY"] = os.environ["BENCHMARKING_AZURE_API_KEY"]

    from .brief_creation_team import benchmark_brief_creation
    from .campaign_creation_team import benchmark_campaign_creation
    from .end2end import benchmark_end2end
    from .websurfer import benchmark_websurfer
    from .weekly_analysis_team import benchmark_weekly_analysis

    benchmarks = {
        "websurfer": benchmark_websurfer,
        "brief_creation": benchmark_brief_creation,
        "campaign_creation": benchmark_campaign_creation,
        "end2end": benchmark_end2end,
        "weekly_analysis": benchmark_weekly_analysis,
    }

    _file_path: Path = Path(file_path)
    while True:
        row: pd.Series
        with lock_file(_file_path):
            df = pd.read_csv(_file_path, index_col=0)

            i = get_random_nan_index(df["status"])
            if i is None:
                print("All tasks are done")
                break

            row = df.iloc[i]
            print(f"Starting with index: {i}")

            df["status"] = df["status"].astype(str)
            df.iloc[i, df.columns.get_loc("status")] = "PENDING"

            df.to_csv(_file_path, index=True)

        kwargs = row.to_dict()
        for k in COMMON_COLUMNS:
            kwargs.pop(k)
        try:
            task = kwargs.pop("task")
            benchmark = benchmarks[task]
            result = run_test(benchmark=benchmark, **kwargs)  # type: ignore[arg-type]

            with lock_file(_file_path):
                df = pd.read_csv(_file_path, index_col=0)
                for k, v in result.items():
                    j = df.columns.get_loc(k)
                    df.iloc[i, j] = v
                df.iloc[i, df.columns.get_loc("status")] = "DONE"

                df.to_csv(_file_path, index=True)

                report_ag_df = create_ag_report(df, groupby_list=GROUP_BY_DICT[task])
                report_ag_path = _file_path.parent / f"{_file_path.stem}-aggregated.csv"
                report_ag_df.to_csv(report_ag_path, index=True)

        except Exception as e:
            # this should never happen unless there is some system error
            with lock_file(_file_path):
                df = pd.read_csv(_file_path, index_col=0)
                df.iloc[i, df.columns.get_loc("status")] = "Unhandled exception"
                df.iloc[i, df.columns.get_loc("output")] = f"{e}"
                df.to_csv(_file_path, index=True)


if __name__ == "__main__":
    app()
