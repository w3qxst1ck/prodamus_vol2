from aiogram.fsm.state import StatesGroup, State


class SendMessagesFSM(StatesGroup):
    text = State()
    media = State()
