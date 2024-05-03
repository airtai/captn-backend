#! /usr/bin/env python

import datetime
import itertools
import os
import random
import time
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Literal, TypeAlias

import pandas as pd
import typer
from filelock import FileLock
from tabulate import tabulate

from ..teams._brief_creation_team import BriefCreationTeam
from .brief_creation_team import URL_SUMMARY_DICT


class Models(str, Enum):
    gpt3_5 = "gpt3-5"
    gpt4 = "gpt4"


app = typer.Typer()

tasks_types: TypeAlias = Literal["websurfer", "brief_creation"]


@contextmanager
def lock_file(path: Path) -> Iterator[None]:
    lock_path = path.parents[0] / f"{path.name}.lock"

    try:
        with FileLock(str(lock_path)):
            yield
    finally:
        lock_path.unlink()


COMMON_COLUMNS = ["execution_time", "status", "success", "output"]


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
        Models.gpt4,
        help="Model which will be used by the web surfer navigator",
    ),
    file_name: str = typer.Option(
        "websurfer-benchmark-tasks.csv",
        help="File name of the task list",
    ),
    repeat: int = typer.Option(
        10,
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
        Models.gpt3_5,
        help="Model which will be used by all agents",
    ),
    file_name: str = typer.Option(
        "brief-creation-benchmark-tasks.csv",
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


def run_test(
    benchmark: Callable[..., Any],
    **kwargs: Any,
) -> Dict[str, Any]:
    try:
        time_start = time.time()
        output = benchmark(**kwargs)
        success = True
    except Exception as e:
        output = str(e)
        success = False
    finally:
        total_time = time.time() - time_start
        status = "DONE"

    return {
        "execution_time": total_time,
        "status": status,
        "success": success,
        "output": output,
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
    group = df.groupby(groupby_list)["success"]
    total = group.count()
    success = group.sum()
    success_rate = (success / total).rename("success_rate")

    group = df.groupby(groupby_list)["execution_time"]
    avg_time = group.mean().rename("avg_time")

    ag_report_df = pd.concat([success_rate, avg_time], axis=1).sort_values(
        "success_rate", ascending=True
    )

    # Calculate total success rate and average time
    total_success = success.sum()
    count = len(df)
    total_time = df["execution_time"].sum()
    total_success_rate = total_success / count
    total_avg_time = total_time / count

    ag_report_df.loc["Total"] = [total_success_rate, total_avg_time]

    # round columns to 2 decimal places
    ag_report_df = ag_report_df.round(2)

    return ag_report_df


GROUP_BY_DICT = {
    "websurfer": ["url"],
    "brief_creation": ["url", "team_name"],
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
    from .websurfer import benchmark_websurfer

    benchmarks = {
        "websurfer": benchmark_websurfer,
        "brief_creation": benchmark_brief_creation,
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
