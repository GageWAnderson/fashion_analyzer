import asyncio
import logging
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


@pytest.fixture(scope="session")
def cleanup(request, run_id: str, test_outputs_dir: Path) -> None:
    """
    Aggregates the test results and outputs a readable report for the run_id.
    """

    def aggregate_results() -> None:
        df = pd.read_csv(f"{test_outputs_dir}/{run_id}.csv")
        if df.empty:
            logger.warning(f"No test results found for run_id: {run_id}")
            return
        create_test_report(df, test_outputs_dir)

    request.addfinalizer(aggregate_results)
