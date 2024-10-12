from pydantic import BaseModel

class FeedbackForm(BaseModel):
    user_id: int
    feedback: str
    rating: int