import functools
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Set

import pandas as pd
import pytest
from pytest import MonkeyPatch
from tabulate import tabulate
from typer.testing import CliRunner

import captn.captn_agents.backend.benchmarking.brief_creation_team
import captn.captn_agents.backend.benchmarking.campaign_creation_team
import captn.captn_agents.backend.benchmarking.end2end
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
        assert "generate-task-table-for-campaign-creation" in result.stdout

    @staticmethod
    def benchmark_success(success: bool, *args, **kwargs):
        print(f"success: {success}")
        if success:
            return "it's ok", 0
        else:
            raise RuntimeError("it's not ok")

    @staticmethod
    def generate_task_table(
        command: str,
        tmp_dir: TemporaryDirectory,
        file_name: str,
        no_rows: int = 50,
        additional_generate_task_table_parameters: Optional[List[str]] = None,
    ):
        final_command = [command, "--output-dir", tmp_dir]
        if additional_generate_task_table_parameters is not None:
            final_command += additional_generate_task_table_parameters

        result = runner.invoke(app, final_command)
        assert result.exit_code == 0, result.stdout

        df = pd.read_csv(Path(tmp_dir) / file_name)
        assert len(df) == no_rows

    @staticmethod
    def run_tests_for_team_success(
        file_name: str,
        command: str,
        aggregated_csv_name: str,
        success: bool,
        columns: Set[str] = [  # noqa: B006
            "Unnamed: 0",
            "url",
            "success_percentage",
            "success_with_retry_percentage",
            "failed_percentage",
            "avg_time",
        ],
        no_rows: int = 50,
        additional_generate_task_table_parameters: Optional[List[str]] = None,
    ) -> None:
        with TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / file_name
            TestBase.generate_task_table(
                command=command,
                file_name=file_name,
                tmp_dir=tmp_dir,
                no_rows=no_rows,
                additional_generate_task_table_parameters=additional_generate_task_table_parameters,
            )

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
                assert (df["success"] == "Success").all()
            else:
                assert (df["success"] == "Failed").all()

            aggregated_csv_path = Path(tmp_dir) / aggregated_csv_name
            assert aggregated_csv_path.exists()

            aggregated_df = pd.read_csv(aggregated_csv_path)
            assert columns == aggregated_df.columns.tolist()


class TestWebsurfer:
    command = "generate-task-table-for-websurfer"
    file_name = "websurfer-benchmark-tasks.csv"
    aggregated_csv_name = "websurfer-benchmark-tasks-aggregated.csv"

    def test_generate_task_table_for_websurfer_success(self):
        with TemporaryDirectory() as tmp_dir:
            TestBase.generate_task_table(
                command=self.command,
                file_name=self.file_name,
                tmp_dir=tmp_dir,
            )

    @pytest.mark.parametrize("success", [True, False])
    def test_run_tests_for_websurfer_success(
        self, success: bool, monkeypatch: MonkeyPatch
    ):
        monkeypatch.setattr(
            captn.captn_agents.backend.benchmarking.websurfer,
            "benchmark_websurfer",
            functools.partial(TestBase.benchmark_success, success),
        )

        TestBase.run_tests_for_team_success(
            command=self.command,
            file_name=self.file_name,
            aggregated_csv_name=self.aggregated_csv_name,
            success=success,
            no_rows=50,
        )

    def test_create_ag_report(self):
        df = pd.DataFrame(
            {
                "url": ["url1", "url2", "url1", "url2", "url1", "url1"],
                "status": ["DONE", "DONE", "DONE", "DONE", "DONE", "DONE"],
                "success": [
                    "Success",
                    "Success with retry",
                    "Failed",
                    "Failed",
                    "Failed",
                    "Failed",
                ],
                "execution_time": [1, 2, 3, 4, 5, 2],
            }
        )
        report_ag_df = captn.captn_agents.backend.benchmarking.base.create_ag_report(
            df, ["url"]
        )

        assert report_ag_df.shape == (3, 5)

        url1_result = report_ag_df[report_ag_df["url"] == "url1"]
        assert url1_result["success_percentage"].values[0] == 25.0
        assert url1_result["failed_percentage"].values[0] == 75.0
        assert url1_result["avg_time"].values[0] == 2.75

        url2_result = report_ag_df[report_ag_df["url"] == "url2"]
        assert url2_result["success_percentage"].values[0] == 0.0
        assert url2_result["success_with_retry_percentage"].values[0] == 50.0
        assert url2_result["failed_percentage"].values[0] == 50.0
        assert url2_result["avg_time"].values[0] == 3.0

        total_result = report_ag_df[report_ag_df["url"] == "Total"]
        assert total_result["success_percentage"].values[0] == 16.67
        assert total_result["success_with_retry_percentage"].values[0] == 16.67
        assert total_result["failed_percentage"].values[0] == 66.67
        assert total_result["avg_time"].values[0] == 2.83

    def test_create_ag_report_with_multiple_columns_to_group_by(self):
        df = pd.DataFrame(
            {
                "url": ["url1", "url2", "url1", "url2", "url1", "url1"],
                "team_name": ["team1", "team1", "team1", "team1", "team2", "team1"],
                "status": ["DONE", "DONE", "DONE", "DONE", "DONE", "DONE"],
                "success": [
                    "Success",
                    "Success with retry",
                    "Failed",
                    "Failed",
                    "Failed",
                    "Failed",
                ],
                "execution_time": [1, 2, 3, 4, 5, 2],
            }
        )
        report_ag_df = captn.captn_agents.backend.benchmarking.base.create_ag_report(
            df, ["url", "team_name"]
        )

        assert report_ag_df.shape == (4, 6)


class TestBriefCreation:
    command = "generate-task-table-for-brief-creation"
    file_name = "brief-creation-benchmark-tasks.csv"
    aggregated_csv_name = "brief-creation-benchmark-tasks-aggregated.csv"

    def test_generate_task_table_for_brief_creation_success(self):
        with TemporaryDirectory() as tmp_dir:
            TestBase.generate_task_table(
                command=self.command,
                file_name=self.file_name,
                tmp_dir=tmp_dir,
                no_rows=100,
            )

    @pytest.mark.parametrize("success", [True, False])
    def test_run_tests_for_brief_creation_success(
        self, success: bool, monkeypatch: MonkeyPatch
    ):
        monkeypatch.setattr(
            captn.captn_agents.backend.benchmarking.brief_creation_team,
            "benchmark_brief_creation",
            functools.partial(TestBase.benchmark_success, success),
        )

        TestBase.run_tests_for_team_success(
            command=self.command,
            file_name=self.file_name,
            aggregated_csv_name=self.aggregated_csv_name,
            success=success,
            no_rows=100,
            columns=[
                "Unnamed: 0",
                "url",
                "team_name",
                "success_percentage",
                "success_with_retry_percentage",
                "failed_percentage",
                "avg_time",
            ],
        )


class TestCampaignCreation:
    command = "generate-task-table-for-campaign-creation"
    file_name = "campaign-creation-benchmark-tasks.csv"
    aggregated_csv_name = "campaign-creation-benchmark-tasks-aggregated.csv"

    def test_generate_task_table_for_campaign_creation_success(self):
        with TemporaryDirectory() as tmp_dir:
            TestBase.generate_task_table(
                command=self.command,
                file_name=self.file_name,
                tmp_dir=tmp_dir,
                no_rows=50,
            )

    @pytest.mark.parametrize("end2end_param", ["--end2end"])  # , "--no-end2end"])
    @pytest.mark.parametrize("success", [True, False])
    def test_run_tests_for_campaign_creation_success(
        self, success: bool, end2end_param: bool, monkeypatch: MonkeyPatch
    ):
        if end2end_param == "--end2end":
            monkeypatch.setattr(
                captn.captn_agents.backend.benchmarking.end2end,
                "benchmark_end2end",
                functools.partial(TestBase.benchmark_success, success),
            )
        else:
            monkeypatch.setattr(
                captn.captn_agents.backend.benchmarking.campaign_creation_team,
                "benchmark_campaign_creation",
                functools.partial(TestBase.benchmark_success, success),
            )

        TestBase.run_tests_for_team_success(
            command=self.command,
            file_name=self.file_name,
            aggregated_csv_name=self.aggregated_csv_name,
            success=success,
            no_rows=50,
            additional_generate_task_table_parameters=[end2end_param],
        )
