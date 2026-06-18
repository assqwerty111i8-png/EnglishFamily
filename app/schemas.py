from pydantic import BaseModel


class CardCreate(BaseModel):
    user_id: int
    front: str
    back: str


class UserCreate(BaseModel):
    name: str
    role: str
    cefr_level: str