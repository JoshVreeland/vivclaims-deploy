from app.database import engine, Base
from app.models import user_model  # ⬅️ import all models here
from .file_model import FileRecord, Admin
from .client_addition import ClientAddition


def init_db():
    Base.metadata.create_all(bind=engine)
