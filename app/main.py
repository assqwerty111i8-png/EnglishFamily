from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates

from app.database import engine, Base, SessionLocal
from app import models
from app.models import User, Card, CardReview
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.routers.cards import router as cards_router
from app.routers.users import router as users_router
from fastapi.responses import RedirectResponse, Response
from uuid import uuid4

def get_current_user(request: Request, db):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return None

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    return user

sessions = {}  # session_id -> user_id

ADMIN_PASSWORD = "Qwerty889900"

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(cards_router)
app.include_router(users_router)

templates = Jinja2Templates(directory="app/templates")

@app.get("/profiles")
def profiles_page(request: Request):

    db = SessionLocal()

    try:

        users = db.query(User).all()

        return templates.TemplateResponse(
            request=request,
            name="profiles.html",
            context={
                "users": users
            }
        )

    finally:
        db.close()

@app.get("/my-profile")
def my_profile(request: Request):
    db = SessionLocal()

    try:
        user = get_current_user(request, db)

        if not user:
            return RedirectResponse("/login")

        return RedirectResponse(f"/user/{user.id}")

    finally:
        db.close()

@app.get("/home")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={}
    )


@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={}
    )


@app.post("/register")
def register_user(
    password: str = Form(...),
    role: str = Form(...),
    cefr_level: str = Form(...)
):
    db = SessionLocal()

    try:

        existing_user = (
            db.query(User)
            .filter(User.role == role)
            .first()
        )

        if existing_user:
            return RedirectResponse(
                url="/login",
                status_code=302
            )

        user = User(
            password=password,
            role=role,
            cefr_level=cefr_level
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        generate_cards_for_user(db, user)

        response = RedirectResponse(
            url=f"/user/{user.id}",
            status_code=302
        )

        response.set_cookie(
            "user_id",
            str(user.id)
        )

        return response

    finally:
        db.close()

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )


@app.post("/login")
def login_user(
    request: Request,
    role: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.role == role).first()

        if not user:
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={"error": "Пользователь не найден"}
            )

        if user.password != password:
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={"error": "Неверный пароль"}
            )

        # 🔐 создаём session
        session_id = str(uuid4())
        sessions[session_id] = user.id

        response = RedirectResponse(
            url=f"/user/{user.id}",
            status_code=302
        )

        response.set_cookie("session_id", session_id, httponly=True)

        return response

    finally:
        db.close()


@app.get("/logout")
def logout(request: Request):

    session_id = request.cookies.get("session_id")

    if session_id in sessions:
        del sessions[session_id]

    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("session_id")

    return response

import random

def generate_cards_for_user(db, user):

    filename = (
        f"app/vocabulary/"
        f"{user.cefr_level.lower()}.txt"
    )

    print("Level:", user.cefr_level)
    print("File:", filename)

    try:

        with open(
            filename,
            encoding="utf-8"
        ) as f:

            words = f.readlines()

        print("Words found:", len(words))

    except Exception as e:

        print("ERROR:", e)
        return

    existing_words = {
        card.front
        for card in db.query(Card)
        .filter(Card.user_id == user.id)
        .all()
    }

    available = []

    for row in words:

        if "|" not in row:
            continue

        front, back = row.strip().split("|")

        if front not in existing_words:
            available.append((front, back))

    random.shuffle(available)

    print("Available words:", len(available))

    for front, back in available[:20]:

        db.add(
            Card(
                user_id=user.id,
                front=front,
                back=back
            )
        )

    db.commit()

@app.get("/admin")
def admin_login(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={}
    )

@app.post("/admin")
def admin_auth(
    password: str = Form(...)
):

    if password == ADMIN_PASSWORD:

        response = RedirectResponse(
            url="/",
            status_code=302
        )

        response.set_cookie(
            "admin",
            "true"
        )

        return response

    return RedirectResponse(
        url="/admin",
        status_code=302
    )

@app.get("/")
def landing(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={}
    )

@app.get("/cards-page")
def cards_page(request: Request):

    db = SessionLocal()

    try:

        cards = db.query(Card).all()

        return templates.TemplateResponse(
            request=request,
            name="cards.html",
            context={
                "cards": cards
            }
        )

    finally:
        db.close()


@app.get("/user/{user_id}")
def user_page(user_id: int, request: Request):

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        cards = (
            db.query(Card)
            .filter(Card.user_id == user_id)
            .all()
        )

        reviews_count = (
            db.query(CardReview)
            .join(Card, Card.id == CardReview.card_id)
            .filter(Card.user_id == user_id)
            .count()
        )

        learned_cards = (
            db.query(Card)
            .filter(
                Card.user_id == user_id,
                Card.review_count >= 3
            )
            .count()
        )

        mature_cards = (
            db.query(Card)
            .filter(
                Card.user_id == user_id,
                Card.stability >= 10
            )
            .count()
        )

        total_reviews = (
            db.query(CardReview)
            .join(Card)
            .filter(Card.user_id == user_id)
            .count()
        )

        success_reviews = (
            db.query(CardReview)
            .join(Card)
            .filter(
                Card.user_id == user_id,
                CardReview.rating >= 3
            )
            .count()
        )

        retention = 0

        if total_reviews > 0:
            retention = round(
                success_reviews / total_reviews * 100
            )

            goal_progress = 0
 
        if user.daily_goal > 0:
            goal_progress = min(
        round(
            user.daily_reviews /
            user.daily_goal * 100
        ),
        100
    )

        return templates.TemplateResponse(
            request=request,
            name="user.html",
            context={
                "user": user,
                "cards": cards,
                "reviews_count": reviews_count,
                "learned_cards": learned_cards,
                "mature_cards": mature_cards,
                "retention": retention,
                "goal_progress": goal_progress
            }
        )

    finally:
        db.close()


@app.get("/study/{user_id}")
def study_page(user_id: int, request: Request):

    return templates.TemplateResponse(
        request=request,
        name="mode_select.html",
        context={
            "user_id": user_id
        }
    )


@app.get("/anki/{user_id}")
def anki_mode(user_id: int, request: Request):

    db = SessionLocal()

    try:

        now = datetime.utcnow()

        card = (
       db.query(Card)
    .filter(
        Card.user_id == user_id,
        (
            (Card.due_date == None) |
            (Card.due_date <= now)
        )
    )
    .order_by(
        Card.due_date.asc().nullsfirst()
    )
    .first()
)

        return templates.TemplateResponse(
            request=request,
            name="anki.html",
            context={
                "card": card,
                "user_id": user_id
            }
        )

    finally:
        db.close()


@app.get("/flashcards/{user_id}")
def flashcards_mode(user_id: int, request: Request):

    db = SessionLocal()

    try:

        card = (
            db.query(Card)
            .filter(Card.user_id == user_id)
            .order_by(Card.id)
            .first()
        )

        return templates.TemplateResponse(
            request=request,
            name="study.html",
            context={
                "card": card,
                "user_id": user_id
            }
        )

    finally:
        db.close()


@app.get("/study/{user_id}/{card_id}")
def study_card(
    user_id: int,
    card_id: int,
    request: Request
):

    db = SessionLocal()

    try:

        card = (
            db.query(Card)
            .filter(
                Card.id == card_id,
                Card.user_id == user_id
            )
            .first()
        )

        total_cards = (
            db.query(Card)
            .filter(Card.user_id == user_id)
            .count()
        )

        current_position = (
            db.query(Card)
            .filter(
                Card.user_id == user_id,
                Card.id <= card_id
            )
            .count()
        )

        return templates.TemplateResponse(
            request=request,
            name="study.html",
            context={
                "card": card,
                "user_id": user_id,
                "total_cards": total_cards,
                "current_position": current_position
            }
        )

    finally:
        db.close()


@app.get("/anki_review/{user_id}/{rating}/{card_id}")
def anki_review(
    user_id: int,
    rating: int,
    card_id: int,
    request: Request
):

    db = SessionLocal()

    try:

        card = (
            db.query(Card)
            .filter(Card.id == card_id)
            .first()
        )

        if card:

            review = CardReview(
                card_id=card.id,
                rating=rating
            )

            db.add(review)

            card.review_count += 1

            user = (
    db.query(User)
    .filter(User.id == user_id)
    .first()
)

            user.daily_reviews += 1

            now = datetime.utcnow()

            card.last_review = now

            if rating == 1:

                card.difficulty += 1
                card.due_date = now + timedelta(minutes=1)

            elif rating == 2:

                card.difficulty += 0.5
                card.due_date = now + timedelta(minutes=10)

            elif rating == 3:

                card.stability += 1
                card.due_date = now + timedelta(days=1)

            elif rating == 4:

                card.stability += 2
                card.due_date = now + timedelta(days=4)

            db.commit()

        return RedirectResponse(
            url=f"/anki/{user_id}",
            status_code=302
        )

    finally:
        db.close()

@app.get("/flash_review/{user_id}/{rating}/{card_id}")
def flash_review(
    user_id: int,
    rating: int,
    card_id: int
):

    db = SessionLocal()

    try:

        next_card = (
            db.query(Card)
            .filter(
                Card.user_id == user_id,
                Card.id > card_id
            )
            .order_by(Card.id)
            .first()
        )

        if next_card:
            return RedirectResponse(
                url=f"/study/{user_id}/{next_card.id}",
                status_code=302
            )

        return RedirectResponse(
            url=f"/user/{user_id}",
            status_code=302
        )

    finally:
        db.close()

@app.get("/stats")
def stats_page(request: Request):

    db = SessionLocal()

    try:

        users_count = db.query(User).count()
        cards_count = db.query(Card).count()
        reviews_count = db.query(CardReview).count()

        learned_cards = (
            db.query(Card)
            .filter(Card.review_count >= 3)
            .count()
        )

        mature_cards = (
            db.query(Card)
            .filter(Card.review_count >= 10)
            .count()
        )

        total_reviews = db.query(CardReview).count()

        success_reviews = (
            db.query(CardReview)
            .filter(CardReview.rating >= 3)
            .count()
        )

        retention = 0

        if total_reviews > 0:
            retention = round(
                success_reviews / total_reviews * 100
            )

        return templates.TemplateResponse(
            request=request,
            name="stats.html",
            context={
                "users_count": users_count,
                "cards_count": cards_count,
                "reviews_count": reviews_count,
                "learned_cards": learned_cards,
                "mature_cards": mature_cards,
                "retention": retention
            }
        )

    finally:
        db.close()

@app.get("/add-user")
def add_user_page(
    request: Request
):

    if request.cookies.get("admin") != "true":
        return RedirectResponse("/admin")

    return templates.TemplateResponse(
        request=request,
        name="add_user.html",
        context={}
    )


@app.post("/create-user")
def create_user_form(
    name: str = Form(...),
    role: str = Form(""),
    cefr_level: str = Form("")
):

    db = SessionLocal()

    try:

        user = User(
            name=name,
            role=role,
            cefr_level=cefr_level
        )

        db.add(user)
        db.commit()

        db.refresh(user)

        generate_cards_for_user(
            db,
            user
        )

        return RedirectResponse(
            url="/",
            status_code=302
        )

    finally:
        db.close()


@app.get("/add-card/{user_id}")
def add_card_page(
    user_id: int,
    request: Request
):

    if request.cookies.get("admin") != "true":
        return RedirectResponse("/admin")

    return templates.TemplateResponse(
        request=request,
        name="add_card.html",
        context={
            "user_id": user_id
        }
    )


@app.post("/add-card/{user_id}")
def create_card(
    user_id: int,
    front: str = Form(...),
    back: str = Form(...)
):

    db = SessionLocal()

    try:

        card = Card(
            user_id=user_id,
            front=front,
            back=back
        )

        db.add(card)
        db.commit()

        return RedirectResponse(
            url=f"/user/{user_id}",
            status_code=302
        )

    finally:
        db.close()