#! /usr/bin/env python

import datetime
import itertools
import random
import time
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, Literal, TypeAlias

import pandas as pd
import typer
from filelock import FileLock
from tabulate import tabulate

from .websurfer import benchmark_websurfer


class Models(str, Enum):
    gpt3_5 = "gpt3-5"
    gpt4 = "gpt4"


app = typer.Typer()

tasks_types: TypeAlias = Literal["websurfer"]


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
    output_dir: str = typer.Option(  # noqa: B008
        "./",
        help="Output directory for the reports",
    ),
) -> None:
    URLS = [
        "https://www.ikea.com/gb/en/",
        "https://www.disneystore.eu",
        "https://www.hamleys.com/",
        "https://www.konzum.hr",
        "https://faststream.airt.ai",
    ]

    timestamps = [
        datetime.datetime.fromisocalendar(year=2024, week=1, day=1)
        + datetime.timedelta(seconds=i)
        for i in range(repeat)
    ]
    params_list = [
        timestamps,
        ["websurfer"],
        URLS,
        [inner_retries],
        [summarizer_llm],
        [llm],
        [navigator_llm],
    ]
    params_names = [
        "timestamp",
        "task",
        "url",
        "inner_retries",
        "summarizer_llm",
        "llm",
        "navigator_llm",
    ]
    # TODO: Fix type-ignore
    data = list(itertools.product(*params_list))  # type: ignore[call-overload]
    df = pd.DataFrame(data=data, columns=params_names)

    _add_common_columns_and_save(df, output_dir=output_dir, file_name=file_name)


def run_test(
    task: tasks_types,
    **kwargs: Any,
) -> Dict[str, Any]:
    benchmarks = {
        "websurfer": benchmark_websurfer,
    }

    benchmark = benchmarks[task]
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


def create_ag_report(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["success"])
    group = df.groupby("url")["success"]
    total = group.count()
    success = group.sum()
    success_rate = (success / total).rename("success_rate")

    group = df.groupby("url")["execution_time"]
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


@app.command()
def run_tests(
    file_path: str = typer.Option(
        ...,
        help="Path to the file with the tasks",
    ),
) -> None:
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
            result = run_test(**kwargs)

            with lock_file(_file_path):
                df = pd.read_csv(_file_path, index_col=0)
                for k, v in result.items():
                    j = df.columns.get_loc(k)
                    df.iloc[i, j] = v
                df.iloc[i, df.columns.get_loc("status")] = "DONE"

                df.to_csv(_file_path, index=True)

                report_ag_df = create_ag_report(df)
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
