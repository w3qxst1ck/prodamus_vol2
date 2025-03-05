from datetime import datetime


def convert_date(date: datetime) -> str:
    """Перевод даты в формат для вывода"""
    return date.date().strftime("%d.%m.%Y")