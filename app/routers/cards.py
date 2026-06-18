from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Card
from app.schemas import CardCreate

router = APIRouter()


@router.post("/cards")
def create_card(card: CardCreate):

    db: Session = SessionLocal()

    new_card = Card(
        user_id=card.user_id,
        front=card.front,
        back=card.back
    )

    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return {
        "id": new_card.id,
        "front": new_card.front,
        "back": new_card.back
    }


@router.get("/cards")
def get_cards():

    db: Session = SessionLocal()

    try:
        cards = db.query(Card).all()

        return [
            {
                "id": card.id,
                "user_id": card.user_id,
                "front": card.front,
                "back": card.back
            }
            for card in cards
        ]

    finally:
        db.close()

        