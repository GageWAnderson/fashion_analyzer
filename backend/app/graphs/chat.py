from functools import partial
from typing import Annotated, Sequence, TypedDict
import operator

from pydantic import BaseModel

from langchain.tools import StructuredTool
from langchain.prompts import PromptTemplate
from langchain_core.messages import ToolMessage, HumanMessage
from langchain_core.language_models import BaseLanguageModel
from langgraph.graph import StateGraph, START, END
from langchain.schema import BaseMessage, SystemMessage
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.graph.state import CompiledStateGraph
from app.core.config import config
from app.services.llm import get_llm
from app.schemas.config import BackendConfig


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# TODO: Re-enable once we have a more reliable prompt
# continue_prompt = PromptTemplate(
#     input_variables=["original_question", "last_message"],
#     template=config.should_continue_prompt,
# )
# async def should_continue(llm: BaseLanguageModel, state: AgentState) -> str:
#     messages = state.get("messages", [])
#     if not messages:
#         return "continue"

#     original_question = messages[
#         0
#     ].content  # TODO: Come up with a better way to track the original question in state
#     last_message = messages[-1]

#     prompt = continue_prompt.format(
#         original_question=original_question, last_message=last_message.content
#     )

#     response = await llm.ainvoke([HumanMessage(content=prompt)])
#     return "end" if "yes" in response.content.strip().lower() else "continue"


def should_continue(state: AgentState) -> str:
    return "continue" if state["messages"][-1].tool_calls else "end"


async def agent(
    model: BaseLanguageModel, tools: list[StructuredTool], state: AgentState
) -> AgentState:
    """
    Selects the tool to call given the messages in the conversation.
    Returns the JSON response with the tool call info to be executed by the action node.
    """
    # Extract the last user message
    last_user_message = next(
        (msg for msg in reversed(state["messages"]) if isinstance(msg, HumanMessage)),
        None,
    )
    if not last_user_message:
        raise ValueError("No user message found in the conversation")

    # Format the tool_call_prompt with the user's question and available tools
    prompt = PromptTemplate(
        template=config.tool_call_prompt, input_variables=["question", "tools"]
    )
    formatted_prompt = prompt.format(
        question=last_user_message.content,
        tools="\n".join(f"- {tool.name}: {tool.description}" for tool in tools),
    )

    # Invoke the model with the formatted prompt
    response = await model.ainvoke([SystemMessage(content=formatted_prompt)])
    return {"messages": state["messages"] + [response]}


async def action(executor: ToolExecutor, state: AgentState) -> AgentState:
    """
    Executes the tool calls from the agent and streams the results back to the client
    through the tool executor.
    """
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        raise ValueError("Last message does not contain tool calls")

    tool_call = last_message.tool_calls[0]
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
    """
    This graph implements a simle ReACT style agent.
    The tool calling LLM first selects the appropriate tool to call given the user's question.
    Then, the appropriate tool is called and the results are streamed back to the user.
    Note that the tools called can be graphs themselves, allowing for complex workflows.
    """

    graph: CompiledStateGraph

    @classmethod
    def from_config(
        cls,
        config: BackendConfig,
        tools: list[StructuredTool],
    ) -> "ChatGraph":
        # should_continue_fn = partial(should_continue, llm)
        graph = StateGraph(AgentState)

        graph.add_node(
            "agent",
            partial(agent, get_llm(config.tool_call_llm).bind_tools(tools), tools),
        )
        graph.add_node("action", partial(action, ToolExecutor(tools)))

        graph.add_edge(START, "agent")
        graph.add_edge("action", "agent")
        graph.add_conditional_edges(
            "agent", should_continue, path_map={"continue": "action", "end": END}
        )

        return graph.compile()
