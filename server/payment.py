import datetime
from pydantic import BaseModel


class ResponseResultPayment(BaseModel):
    """Поля из ответа сервера Prodamus"""
    tg_id: str
    payment_status: str
    sing_is_good: bool
    customer_phone: str
    profile_id: str
    date_last_payment: datetime.datetime
    date_next_payment: datetime.datetime


class ResponseResultAutoPay(BaseModel):
    """Данные из тела ответа по автоплатежу"""
    tg_id: str
    profile_id: str
    sing_is_good: bool
    customer_phone: str
    date_last_payment: datetime.datetime
    date_next_payment: datetime.datetime
    action_code: str | None
    error_code: str | None
    error: str | None
    current_attempt: str | None
    last_attempt: str | None
    action_type: str | None
