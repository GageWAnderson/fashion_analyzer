import logging
import time
import asyncio
import pandas as pd
from pathlib import Path

import pytest
import numpy as np
from langchain_core.messages import HumanMessage

from backend.app.graphs.chat import ChatGraph
from backend.app.schemas.agent_state import AgentState
from backend.app.config.config import backend_config

CUTOFF = 0.9
logger = logging.getLogger(__name__)


@pytest.mark.asyncio(loop_scope="session")
async def test_router(
    test_data_df: pd.DataFrame,
    run_id: str,
    test_outputs_dir: Path,
) -> None:
    chat_graph = await ChatGraph.from_config(backend_config)
    tasks = [
        _test_router(row["question"], row["tool"], chat_graph)
        for _, row in test_data_df.iterrows()
    ]
    results = await asyncio.gather(*tasks)
    router_accuracy = _get_router_accuracy(results)
    logger.info(f"Router accuracy: {router_accuracy}")
    df = pd.DataFrame(results)
    df.to_csv(test_outputs_dir / f"router_tool_results_{run_id}.csv", index=False)
    assert router_accuracy > CUTOFF


async def _test_router(question: str, tool: str, chat_graph: ChatGraph) -> dict:
    duration = np.nan
    passed = False
    selected_subgraph = None
    subgraph_selector_test_state = AgentState(
        user_question=question,
        messages=[HumanMessage(content=question)],
        selected_tool="",
    )
    try:
        start_time = time.time()
        selected_subgraph = await chat_graph.select_subgraph(
            chat_graph.llm, chat_graph.subgraphs, subgraph_selector_test_state
        )
        end_time = time.time()
        logger.info(f"Selected subgraph: {selected_subgraph}")
        duration = end_time - start_time
        passed = selected_subgraph == tool
    except Exception as e:
        logger.exception(f"Error selecting tool for question: {question}")
    finally:
        return {
            "duration": duration,
            "passed": passed,
            "question": question,
            "expected_output": tool,
            "output": selected_subgraph,
        }


def _get_router_accuracy(results: list[dict]) -> float:
    return round(
        sum(1 for result in results if result["passed"] is True) / len(results),
        ndigits=2,
    )
