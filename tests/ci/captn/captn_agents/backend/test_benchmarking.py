import functools
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pytest
from pytest import MonkeyPatch
from tabulate import tabulate
from typer.testing import CliRunner

import captn.captn_agents.backend.benchmarking.base
from captn.captn_agents.backend.benchmarking.base import (
    app,
)

runner = CliRunner()


class TestWebsurfer:
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage: root [OPTIONS]" in result.stdout
        assert "generate-task-table-for-websurfer" in result.stdout

    @staticmethod
    def _generate_task_table_for_websurfer(tmp_dir: TemporaryDirectory):
        result = runner.invoke(
            app, ["generate-task-table-for-websurfer", "--output-dir", tmp_dir]
        )
        assert result.exit_code == 0, result.stdout

        df = pd.read_csv(Path(tmp_dir) / "websurfer-benchmark-tasks.csv")
        assert len(df) == 50

    def test_generate_task_table_for_websurfer_success(self):
        with TemporaryDirectory() as tmp_dir:
            TestWebsurfer._generate_task_table_for_websurfer(tmp_dir)

    @pytest.mark.parametrize("success", [True, False])
    def test_run_tests_for_websurfer_success(
        self, success: bool, monkeypatch: MonkeyPatch
    ):
        def benchmark_websurfer_success(success: bool, *args, **kwargs):
            if success:
                time.sleep(0.001)
                return "it's ok"
            else:
                raise RuntimeError("it's not ok")

        monkeypatch.setattr(
            captn.captn_agents.backend.benchmarking.base,
            "benchmark_websurfer",
            functools.partial(benchmark_websurfer_success, success),
        )

        with TemporaryDirectory() as tmp_dir:
            TestWebsurfer._generate_task_table_for_websurfer(tmp_dir)

            result = runner.invoke(
                app,
                [
                    "run-tests",
                    "--file-path",
                    str(Path(tmp_dir) / "websurfer-benchmark-tasks.csv"),
                ],
            )
            assert result.exit_code == 0, result.stdout

            df = pd.read_csv(
                Path(tmp_dir) / "websurfer-benchmark-tasks.csv", index_col=0
            )
            print(tabulate(df, headers="keys", tablefmt="pretty"))
            assert (df["status"] == "DONE").all()
            if success:
                assert df["success"].all()
            else:
                assert not df["success"].any()

            aggregated_csv_path = (
                Path(tmp_dir) / "websurfer-benchmark-tasks-aggregated.csv"
            )
            assert aggregated_csv_path.exists()

            aggregated_df = pd.read_csv(aggregated_csv_path)
            assert ["url", "success_rate", "avg_time"] == aggregated_df.columns.tolist()

    def test_create_ag_report(self):
        df = pd.DataFrame(
            {
                "url": ["url1", "url2", "url1", "url2", "url1", "url1"],
                "status": ["DONE", "DONE", "DONE", "DONE", "DONE", "DONE"],
                "success": [True, True, False, False, False, False],
                "execution_time": [1, 2, 3, 4, 5, 2],
            }
        )
        report_ag_df = captn.captn_agents.backend.benchmarking.base.create_ag_report(df)

        assert report_ag_df.shape == (3, 2)

        assert report_ag_df.loc["url1", "success_rate"] == 0.25
        assert report_ag_df.loc["url1", "avg_time"] == 2.75
        assert report_ag_df.loc["url2", "success_rate"] == 0.5
        assert report_ag_df.loc["url2", "avg_time"] == 3.0
        assert report_ag_df.loc["Total", "success_rate"] == 0.33
        assert report_ag_df.loc["Total", "avg_time"] == 2.83
