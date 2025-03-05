import datetime
from pydantic import BaseModel


class UserAdd(BaseModel):
    tg_id: str
    username: str | None
    firstname: str | None
    lastname: str | None
    phone: str | None = None


class User(UserAdd):
    id: int


class UserRel(User):
    subscription: list["Subscription"]


class Subscription(BaseModel):
    id: int
    active: bool
    start_date: datetime.datetime | None
    expire_date: datetime.datetime | None
    profile_id: str | None


class SubscriptionRel(Subscription):
    user: list["User"]


class Operations(BaseModel):
    """Операции пользователей подписки/отписки/покупки"""
    tg_id: str
    type: str
    date: datetime.datetime



