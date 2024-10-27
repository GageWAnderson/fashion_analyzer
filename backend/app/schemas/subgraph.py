from pydantic import BaseModel, ConfigDict, Field

from langgraph.graph.state import CompiledStateGraph


class SubgraphSelectionResponse(BaseModel):
    subgraph_name: str = Field(..., description="The name of the subgraph to select")


class Subgraph(BaseModel):
    name: str = Field(..., description="The name of the subgraph")
    description: str = Field(..., description="A description of the subgraph")
    graph: CompiledStateGraph = Field(
        ..., description="The compiled state graph of the subgraph"
    )
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def get_description(cls) -> str:
        return cls.description

    @classmethod
    def get_name(cls) -> str:
        return cls.name
