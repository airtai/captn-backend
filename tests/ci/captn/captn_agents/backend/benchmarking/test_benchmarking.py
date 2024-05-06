import functools
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, List

import pandas as pd
import pytest
from pytest import MonkeyPatch
from tabulate import tabulate
from typer.testing import CliRunner

import captn.captn_agents.backend.benchmarking.brief_creation_team
import captn.captn_agents.backend.benchmarking.websurfer
from captn.captn_agents.backend.benchmarking.base import (
    app,
)

runner = CliRunner()


class TestBase:
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "root [OPTIONS]" in result.stdout
        assert "generate-task-table-for-websurfer" in result.stdout
        assert "generate-task-table-for-brief-creation" in result.stdout

    @staticmethod
    def benchmark_success(success: bool, *args, **kwargs):
        print(f"success: {success}")
        if success:
            return "it's ok"
        else:
            raise RuntimeError("it's not ok")

    @staticmethod
    def run_tests_for_team_success(
        file_name: str,
        aggregated_csv_name: str,
        success: bool,
        generate_table_f: Callable[..., Any],
        columns: List[str] = ["url", "success_rate", "avg_time"],  # noqa: B006
    ) -> None:
        with TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / file_name
            generate_table_f(tmp_dir, file_name)

            result = runner.invoke(
                app,
                [
                    "run-tests",
                    "--file-path",
                    str(file_path),
                ],
            )
            assert result.exit_code == 0, result.stdout

            df = pd.read_csv(file_path, index_col=0)
            print(tabulate(df, headers="keys", tablefmt="pretty"))
            assert (df["status"] == "DONE").all()
            if success:
                assert df["success"].all()
            else:
                assert not df["success"].any()

            aggregated_csv_path = Path(tmp_dir) / aggregated_csv_name
            assert aggregated_csv_path.exists()

            aggregated_df = pd.read_csv(aggregated_csv_path)
            assert columns == aggregated_df.columns.tolist()


class TestWebsurfer:
    @staticmethod
    def _generate_task_table_for_websurfer(
        tmp_dir: TemporaryDirectory, file_name: str = "websurfer-benchmark-tasks.csv"
    ):
        result = runner.invoke(
            app, ["generate-task-table-for-websurfer", "--output-dir", tmp_dir]
        )
        assert result.exit_code == 0, result.stdout

        df = pd.read_csv(Path(tmp_dir) / file_name)
        assert len(df) == 50

    def test_generate_task_table_for_websurfer_success(self):
        with TemporaryDirectory() as tmp_dir:
            TestWebsurfer._generate_task_table_for_websurfer(tmp_dir)

    @pytest.mark.parametrize("success", [True, False])
    def test_run_tests_for_websurfer_success(
        self, success: bool, monkeypatch: MonkeyPatch
    ):
        monkeypatch.setattr(
            captn.captn_agents.backend.benchmarking.websurfer,
            "benchmark_websurfer",
            functools.partial(TestBase.benchmark_success, success),
        )

        file_name = "websurfer-benchmark-tasks.csv"
        aggregated_csv_name = "websurfer-benchmark-tasks-aggregated.csv"

        TestBase.run_tests_for_team_success(
            file_name,
            aggregated_csv_name,
            success,
            generate_table_f=TestWebsurfer._generate_task_table_for_websurfer,
        )

    def test_create_ag_report(self):
        df = pd.DataFrame(
            {
                "url": ["url1", "url2", "url1", "url2", "url1", "url1"],
                "status": ["DONE", "DONE", "DONE", "DONE", "DONE", "DONE"],
                "success": [True, True, False, False, False, False],
                "execution_time": [1, 2, 3, 4, 5, 2],
            }
        )
        report_ag_df = captn.captn_agents.backend.benchmarking.base.create_ag_report(
            df, ["url"]
        )

        assert report_ag_df.shape == (3, 2)

        assert report_ag_df.loc["url1", "success_rate"] == 0.25
        assert report_ag_df.loc["url1", "avg_time"] == 2.75
        assert report_ag_df.loc["url2", "success_rate"] == 0.5
        assert report_ag_df.loc["url2", "avg_time"] == 3.0
        assert report_ag_df.loc["Total", "success_rate"] == 0.33
        assert report_ag_df.loc["Total", "avg_time"] == 2.83


class TestBriefCreation:
    @staticmethod
    def _generate_task_table_for_brief_creation(
        tmp_dir: TemporaryDirectory,
        file_name: str = "brief-creation-benchmark-tasks.csv",
    ):
        result = runner.invoke(
            app, ["generate-task-table-for-brief-creation", "--output-dir", tmp_dir]
        )
        assert result.exit_code == 0, result.stdout

        df = pd.read_csv(Path(tmp_dir) / file_name)
        assert len(df) == 100

    def test_generate_task_table_for_brief_creation_success(self):
        with TemporaryDirectory() as tmp_dir:
            TestBriefCreation._generate_task_table_for_brief_creation(tmp_dir)

    @pytest.mark.parametrize("success", [True, False])
    def test_run_tests_for_brief_creation_success(
        self, success: bool, monkeypatch: MonkeyPatch
    ):
        monkeypatch.setattr(
            captn.captn_agents.backend.benchmarking.brief_creation_team,
            "benchmark_brief_creation",
            functools.partial(TestBase.benchmark_success, success),
        )

        file_name = "brief-creation-benchmark-tasks.csv"
        aggregated_csv_name = "brief-creation-benchmark-tasks-aggregated.csv"

        TestBase.run_tests_for_team_success(
            file_name,
            aggregated_csv_name,
            success,
            generate_table_f=TestBriefCreation._generate_task_table_for_brief_creation,
            columns=["Unnamed: 0", "success_rate", "avg_time"],
        )
