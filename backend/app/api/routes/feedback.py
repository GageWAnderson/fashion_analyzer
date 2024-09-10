from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.feedback import FeedbackForm
from app.db.session import get_db
from app.db.models import Feedback

router = APIRouter()

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackForm, db: Session = Depends(get_db)):
    new_feedback = Feedback(user_id=feedback.user_id, feedback=feedback.feedback, rating=feedback.rating)
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return {"message": "Feedback submitted successfully"}


@router.get("/feedback/{user_id}")
async def get_user_feedback(user_id: int, db: Session = Depends(get_db)):
    user_feedback = db.query(Feedback).filter(Feedback.user_id == user_id).all()
    if not user_feedback:
        raise HTTPException(status_code=404, detail="No feedback found for this user")
    return [{"id": feedback.id, "feedback": feedback.feedback, "rating": feedback.rating} for feedback in user_feedback]

