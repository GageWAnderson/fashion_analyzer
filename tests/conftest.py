import asyncio
import logging
import os
import uuid
from asyncio import AbstractEventLoopPolicy
from pathlib import Path

import pytest
import pandas as pd

from backend.app.config.config import BackendConfig
from tests.utils.create_report import create_test_report
from backend.app.config.config import backend_config

logger = logging.getLogger(__name__)

# Set the event loop scope for async fixtures
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop_policy() -> AbstractEventLoopPolicy:
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="session")
def set_test_env():
    """
    Sets the environment variables for the test suite.
    """
    os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
    yield
    del os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"]


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def test_data_df(test_data_dir: Path) -> pd.DataFrame:
    return pd.read_csv(test_data_dir / "test_cases.csv")


@pytest.fixture(scope="session")
def run_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture(scope="session")
def test_outputs_dir() -> Path:
    return Path(__file__).parent / "test_outputs"


@pytest.fixture(scope="session", autouse=True)
def cleanup(
    request: pytest.FixtureRequest, run_id: str, test_outputs_dir: Path
) -> None:
    """
    Aggregates the test results and outputs a readable report for the run_id.
    """

    def aggregate_results() -> None:
        df = aggregate_test_results(test_outputs_dir, run_id)
        if df.empty:
            logger.warning(f"No test results found for run_id: {run_id}")
            return
        df.to_csv(
            test_outputs_dir / f"aggregated_test_results_{run_id}.csv", index=False
        )
        create_test_report(df, test_outputs_dir)

    request.addfinalizer(aggregate_results)


def aggregate_test_results(test_outputs_dir: Path, run_id: str) -> pd.DataFrame:
    """
    Reads the test output files from all the tools into one DF to generate a report.
    Handles missing files gracefully.
    """
    dfs = []

    result_files = {
        "router": f"router_tool_results_{run_id}.csv",
        "graph": f"graph_results_{run_id}.csv",
    }

    for test_type, filename in result_files.items():
        df = _try_read_results(test_outputs_dir / filename, test_type)
        if df is not None:
            dfs.append(df)

    if not dfs:
        logger.warning("No test results could be loaded")
        return pd.DataFrame()  # Return empty DataFrame if no results

    return pd.concat(dfs, ignore_index=True)


def _try_read_results(file_path: Path, test_type: str) -> pd.DataFrame | None:
    """Helper function to read a single results file."""
    try:
        if file_path.exists():
            return pd.read_csv(file_path)
        else:
            logger.warning(f"{test_type.title()} results file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error reading {test_type} results: {e}")
    return None
