from sqlalchemy import Column, Integer, String, Text
from app.db.base_class import Base

class Feedback(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    feedback = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)