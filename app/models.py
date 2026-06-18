from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Float

from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    password = Column(String, nullable=False)

    role = Column(String)

    cefr_level = Column(String)

    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    daily_reviews = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    daily_goal = Column(Integer, default=50)


class GrammarTopic(Base):
    __tablename__ = "grammar_topics"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False
    )

    description = Column(Text)


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    front = Column(
        String,
        nullable=False
    )

    back = Column(
        String,
        nullable=False
    )

    grammar_topic_id = Column(
        Integer,
        ForeignKey("grammar_topics.id"),
        nullable=True
    )

    review_count = Column(
        Integer,
        default=0
    )

    stability = Column(
        Float,
        default=0
    )

    difficulty = Column(
        Float,
        default=0
    )

    due_date = Column(
        DateTime,
        nullable=True
    )

    last_review = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class CardReview(Base):
    __tablename__ = "card_reviews"

    id = Column(Integer, primary_key=True)

    card_id = Column(
        Integer,
        ForeignKey("cards.id")
    )

    rating = Column(Integer)

    reviewed_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class UserMemory(Base):
    __tablename__ = "user_memory"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    cards_learned = Column(
        Integer,
        default=0
    )

    reviews_done = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

