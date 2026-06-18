from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User
from app.schemas import UserCreate

router = APIRouter()


@router.post("/users")
def create_user(user: UserCreate):

    db: Session = SessionLocal()

    new_user = User(
        name=user.name,
        role=user.role,
        cefr_level=user.cefr_level
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "name": new_user.name,
        "role": new_user.role,
        "cefr_level": new_user.cefr_level
    }


@router.get("/users")
def get_users():

    db: Session = SessionLocal()

    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "cefr_level": user.cefr_level
        }
        for user in users
    ]