import logging
from typing import Sequence, Any

from langchain_core.language_models import BaseLanguageModel
from langchain.schema import AIMessage
from langchain_core.tools import BaseTool
from langchain_core.runnables import Runnable
from langchain.schema.runnable import RunnableConfig
from langchain_core.prompts import PromptTemplate

from backend.app.schemas.agent_state import AgentState
from backend.app.config.config import backend_config

logger = logging.getLogger(__name__)


class AgentNode(Runnable[AgentState, AgentState]):
    def __init__(self, llm: BaseLanguageModel, tools: Sequence[BaseTool]):
        self.llm = llm
        self.tools = tools
        self.llm.bind_tools(tools)

    def invoke(self, state: AgentState) -> AgentState:
        raise NotImplementedError("AgentNode does not support sync invoke")

    async def ainvoke(
        self,
        state: AgentState,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AgentState:
        """
        Selects the tool to call given the messages in the conversation.
        Returns the JSON response with the tool call info to be executed by the action node.
        """
        tool_call_prompt = PromptTemplate(
            input_variables=["tools", "question"],
            template=backend_config.tool_call_prompt,
        )

        response = await self.llm.ainvoke(
            tool_call_prompt.format(
                tools=self.tools, question=state["messages"][-1].content
            )
        )
        tool_calls = response.tool_calls
        if not isinstance(response, AIMessage):
            raise ValueError("Agent response is not an AIMessage")
        if not tool_calls:
            raise ValueError("No tool calls found in agent response.")

        tool_names = {tool.name for tool in self.tools}
        if not all(tool_call["name"] in tool_names for tool_call in tool_calls):
            invalid_tool = next(
                tool_call["name"]
                for tool_call in response.tool_calls
                if tool_call["name"] not in tool_names
            )
            raise ValueError(
                f"Chosen tool '{invalid_tool}' is not in the list of available tools"
            )

        return {"messages": state["messages"] + [response]}
