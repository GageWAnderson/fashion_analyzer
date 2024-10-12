from pydantic import BaseModel, Field


class ShouldContinueResponse(BaseModel):
    """
    Your decision on whether you have fully answered the user's questions.
    Return true if you have fully answered the user's questions, false otherwise.
    """
    should_continue: bool = Field(..., description="Whether the agent should continue")
