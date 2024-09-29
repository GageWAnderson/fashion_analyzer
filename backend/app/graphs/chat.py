from functools import partial
from typing import Annotated, Sequence, TypedDict
import operator

from pydantic import BaseModel

from langchain.tools import StructuredTool
from langchain_core.messages import ToolMessage
from langchain_core.language_models import BaseLanguageModel
from langgraph.graph import StateGraph, START, END
from langchain.schema import BaseMessage
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.graph.state import CompiledStateGraph


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


def should_continue(state: AgentState) -> bool:
    return "continue" if state.get("messages", [])[-1].tool_calls else "end"


async def agent(model: BaseLanguageModel, state: AgentState) -> AgentState:
    return {"messages": [await model.ainvoke(state["messages"])]}


async def action(executor: ToolExecutor, state: AgentState) -> AgentState:
    return {
        "messages": [
            ToolMessage(
                tool_call_id=(tool_call := state["messages"][-1]).tool_calls[0].id,
                name=(
                    action := ToolInvocation(
                        tool=tool_call.get("name"), tool_input=tool_call["args"]
                    )
                ).tool,
                content=str(await executor.ainvoke(action)),
            )
        ]
    }


class ChatGraph(BaseModel):
    graph: CompiledStateGraph

    @classmethod
    def from_dependencies(
        cls,
        llm: BaseLanguageModel,
        tools: list[StructuredTool],
    ) -> "ChatGraph":
        graph = StateGraph(AgentState)
        graph.add_node("agent", partial(agent, llm.bind_tools(tools)))
        graph.add_node("action", partial(action, ToolExecutor(tools)))
        graph.add_edge(START, "agent")
        graph.add_conditional_edges(
            "agent", should_continue, {"continue": "action", "end": END}
        )
        graph.add_edge("action", "agent")
        return graph.compile()
