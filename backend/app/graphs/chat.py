from functools import partial
from typing import Annotated, Sequence, TypedDict
import operator

from pydantic import BaseModel

from langchain.tools import StructuredTool
from langchain.prompts import PromptTemplate
from langchain_core.messages import ToolMessage, HumanMessage
from langchain_core.language_models import BaseLanguageModel
from langgraph.graph import StateGraph, START, END
from langchain.schema import BaseMessage
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.graph.state import CompiledStateGraph


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# TODO: Move this to a yaml config file
SHOULD_CONTINUE_PROMPT = PromptTemplate(
    input_variables=["original_question", "last_message"],
    template="""Given the user's original question: "{original_question}"
and the last message in the conversation:
{last_message}

Is the agent's task complete? Answer with 'Yes' if the task is done, or 'No' if more actions or information are needed."""
)

async def should_continue(llm: BaseLanguageModel, state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return "continue"

    original_question = messages[
        0
    ].content  # TODO: Come up with a better way to track the original question in state
    last_message = messages[-1]

    prompt = SHOULD_CONTINUE_PROMPT.format(
        original_question=original_question,
        last_message=last_message.content
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    print(response.content.strip().lower())
    return "end" if "yes" in response.content.strip().lower() else "continue"


async def agent(model: BaseLanguageModel, state: AgentState) -> AgentState:
    return {"messages": [await model.ainvoke(state["messages"])]}


async def action(executor: ToolExecutor, state: AgentState) -> AgentState:
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        raise ValueError("Last message does not contain tool calls")

    tool_call = last_message.tool_calls[0]
    print(tool_call)
    return {
        "messages": [
            ToolMessage(
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
                content=str(
                    await executor.ainvoke(
                        ToolInvocation(
                            tool=tool_call["name"], tool_input=tool_call["args"]
                        )
                    )
                ),
            )
        ]
    }


class ChatGraph:
    graph: CompiledStateGraph

    @classmethod
    def from_dependencies(
        cls,
        llm: BaseLanguageModel,
        tools: list[StructuredTool],
    ) -> "ChatGraph":
        should_continue_fn = partial(should_continue, llm)
        graph = StateGraph(AgentState)
        graph.add_node("agent", partial(agent, llm.bind_tools(tools)))
        graph.add_node("action", partial(action, ToolExecutor(tools)))
        graph.add_edge(START, "agent")
        graph.add_conditional_edges(
            "action", should_continue_fn, path_map={"continue": "agent", "end": END}
        )
        graph.add_edge("agent", "action")
        return graph.compile()
