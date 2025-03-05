import datetime

from database.schemas import UserRel
from routers.utils import convert_date
from settings import settings


def get_welcome_message() -> str:
    """Приветственное сообщение"""
    message = "<b>Нажмите кнопку «Оформить подписку» и оплатите свое участие в закрытом канале с ежедневным питанием от Шевы.</b>\n\n"\
              "Подписка ежемесячная. Вы можете отписаться в любой момент через этот бот.\n\n" \
              "<b>📌 Что вас ждет:</b>\n- Ежедневные планы питания\n- Подробные рецепты с пошаговыми инструкциями\n- Не банальный и вкусный рацион, которой меняется ежедневно\n"\
              "- Инструкция по адаптации приемов пищи под ваш калораж\n- Каждый месяц делаем упор на новую группу продуктов, для разнообразия\n\n" \
              "Особенность канала – универсальная система подстройки рецептов под любой калораж и ежедневные рецепты\n\n" \
              "<b>После оплаты вы будете добавлены в закрытый канал, заявка будет одобрена автоматически.</b>\n\n↓↓↓"
    return message


def welcome_message_second() -> str:
    """Сообщение для тех у кого уже была"""
    message = "Для восстановления подписки на канал с ежедневным питанием от Шевы нажмите кнопку «Оформить подписку».\n\n" \
              "<b>Возобновите доступ к:</b>\n" \
              "- Авторским планам питания на каждый день\n- Рецептам с подробными инструкциями\n- Разнообразному и вкусному рациону\n" \
              "- Гибкой системе под ваш калораж\n- Сезонным питанием\n- Списком закупа продуктов на неделю\n\n" \
              "<i>Автоматическое добавление в канал после оплаты. Подпиской управляете через бот.</i>"
    return message

def subscribe_message() -> str:
    """Сообщение об условиях подписки"""
    message = "Вы оформляете ежемесячную подписку на закрытый канал с ежедневным питанием от Шевы.\n\n" \
              "💰<b>Стоимость: 890 руб/месяц</b>\n\n" \
              "При успешной оплате ссылка на вступление в канал придет в течение 5 минут\n\n" \
              "Для оформления подписки оплатите по ссылке ниже\n\n" \
              "↓↓↓"
    return message


def get_status_message(is_active: bool, expire_date: datetime.datetime) -> str:
    """Status message"""

    # подписка активна
    if is_active:
        message = "Статус подписки на закрытый канал с ежедневным питанием от Шевы:\n\n" \
                  "✅ Подписка активна\n\n" \
                  f"Доступ к каналу открыт до {convert_date(expire_date)}\n" \
                  f"Следующее списание {convert_date(expire_date - datetime.timedelta(days=1))}\n\n" \
                  f"*<i>Вы всегда можете отменить подписку через меню бота</i>"

    # если подписка неактивна
    else:
        # если оплаченный срок еще не вышел
        if expire_date is not None and expire_date.date() >= datetime.datetime.now().date():
            message = "Статус подписки на закрытый канал с ежедневным питанием от Шевы:\n\n" \
                      "⛔️ Подписка отменена\n" \
                      f"⚠️ Доступ к каналу открыт до {convert_date(expire_date)}\n\n" \
                      f"<i>*Вы сможете оформить подписку заново после завершения {convert_date(expire_date)}</i>"
        # если подписка уже кончилась
        else:
            message = "Статус подписки на закрытый канал с ежедневным питанием от Шевы:\n\n" \
                      "⛔️ Подписка неактивна\n\n" \
                      f"*<i>Вы можете оформить подписку заново через команду /oplata</i>"

    return message


def get_cancel_subscribe_message(expire_date: datetime.datetime) -> str:
    """Сообщение об отмене подписки"""
    message = "⛔️ Ваша подписка отменена\n\n" \
              f"Доступ к каналу будет прекращён: {convert_date(expire_date)}.\n\n" \
              f"Вы всегда можете оформить подписку заново с помощью команды /oplata"

    return message


def get_vopros_message() -> str:
    """Help message"""
    message = "Если у тебя есть какие-то технические вопросы или проблемы с оплатой напиши нашему менеджеру " \
              "@andrey_vismon - он поможет с вашей проблемой или ответит на ваши вопросы."
    return message