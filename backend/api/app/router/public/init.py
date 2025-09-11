from fastapi import APIRouter
from app.schemas.user import UserCreate, UserRead
from app.core.typing import DbDep
from app.models import User

router = APIRouter()

@router.post("/users", response_model=UserRead)
def create_user(user: UserCreate, db: DbDep) -> UserRead:

@router.get("/healthz")
def healthz():
    return {"status": "ok"}
