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

    def test_generate_task_table_for_websurfer_success(self):
        with TemporaryDirectory() as tmp_dir:
            result = runner.invoke(
                app, ["generate-task-table-for-websurfer", "--output-dir", tmp_dir]
            )
            assert result.exit_code == 0, result.stdout

            df = pd.read_csv(Path(tmp_dir) / "websurfer-benchmark-tasks.csv")
            assert len(df) == 50

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
            result = runner.invoke(
                app, ["generate-task-table-for-websurfer", "--output-dir", tmp_dir]
            )
            assert result.exit_code == 0, result.stdout

            df = pd.read_csv(Path(tmp_dir) / "websurfer-benchmark-tasks.csv")
            assert len(df) == 50

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
