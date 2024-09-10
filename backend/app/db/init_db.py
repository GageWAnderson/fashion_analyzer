from app.db.base_class import Base
from app.db.session import engine
from app.db.models import Feedback  # Ensure this is imported

Base.metadata.create_all(bind=engine)