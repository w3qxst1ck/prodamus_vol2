from datetime import timedelta, datetime

import requests
from fastapi import FastAPI, Request
from starlette import status

from server.payment import ResponseResultPayment, ResponseResultAutoPay
from server.logger import logger
from server.services import get_body_params_pay_success, get_body_params_auto_pay
from database.orm import AsyncOrm
from server import messages as ms
from settings import settings


app = FastAPI()


@app.get("/ping")
async def root():
    logger.info("Log from ping api")
    return {"message": "some message"}


@app.get("/test")
async def root():
    response = requests.get("https://httpbin.org/ip").json()
    logger.warning("Log from test")
    print(response)
    return {"response": response}


# ПОКУПКА ПОДПИСКИ
@app.post("/success_pay", status_code=status.HTTP_200_OK)
async def buy_subscription(request: Request):
    response: ResponseResultPayment = await get_body_params_pay_success(request)

    # проверка на успешный платеж
    if not(response.sing_is_good and response.payment_status == "success"):
        await ms.buy_subscription_error(int(response.tg_id))
        logger.error(f"Ошибка при покупке подписки у пользователя tg_id {response.tg_id}")

    # успешная оплата
    else:
        user = await AsyncOrm.get_user_with_subscription_by_tg_id(response.tg_id)

        # создаем и отправляем ссылку на вступление в группу
        invite_link = await ms.generate_invite_link(user)
        await ms.send_invite_link_to_user(int(user.tg_id), invite_link, expire_date=response.date_next_payment)

        # обновляем телефон
        await AsyncOrm.add_user_phone(user.id, response.customer_phone)

        # меняем дату окончания подписки
        await AsyncOrm.update_subscribe(
            subscription_id=user.subscription[0].id,
            start_date=response.date_last_payment,
            expire_date=response.date_next_payment + timedelta(days=1, hours=1),    # запас по времени 1 день и 1 час
            profile_id=response.profile_id
        )

        # учет операции
        await AsyncOrm.add_operation(user.tg_id, "BUY_SUB", response.date_last_payment)
        logger.info(f"Пользователь с tg id {user.tg_id}, телефон {response.customer_phone} купил подписку")


# АВТОПЛАТЕЖ ПО ПОДПИСКЕ
@app.post("/auto_pay", status_code=status.HTTP_200_OK)
async def auto_pay_subscription(request: Request):
    """Прием автоплатежа по подписке"""
    response: ResponseResultAutoPay = await get_body_params_auto_pay(request)

    # неуспешные автоплатежи
    if not response.sing_is_good or response.error:
        user = await AsyncOrm.get_user_with_subscription_by_tg_id(response.tg_id)

        if not response.sing_is_good:
            logger.error(f"Автоплатеж не прошел tg_id {response.tg_id} | ошибка проверки подписи")
        else:
            logger.error(f"Автоплатеж платеж не прошел tg id {response.tg_id} | prodamus error: {response.error}")

        # оповещаем пользователя при первой неудачной попытке списания
        if response.current_attempt == "1" and response.action_type == "notification":
            await ms.send_auto_pay_error_message_to_user(user)

        # при последней неудачной попытке списания и отмене подписки в продамусе
        if response.last_attempt == "yes" and response.action_code == "deactivation":
            # деактивируем подписку
            await AsyncOrm.deactivate_subscription(user.id)

            # кикаем из канала
            await ms.delete_user_from_channel(settings.channel_id, int(user.tg_id))

            # оповещаем пользователя, что подписка кончилась
            await ms.send_error_message_to_user(int(user.tg_id))

            # учитываем отмену подписки
            await AsyncOrm.add_operation(user.tg_id, "AUTO_UN_SUB", datetime.now())

    # успешные автоплатежи
    elif response.action_type == "action" and response.action_code == "auto_payment":
        user = await AsyncOrm.get_user_with_subscription_by_tg_id(response.tg_id)

        # оповещаем пользователя
        await ms.send_success_message_to_user(int(response.tg_id), response.date_next_payment)

        # меняем дату окончания подписки
        await AsyncOrm.update_subscribe(
            subscription_id=user.subscription[0].id,
            start_date=response.date_last_payment,
            expire_date=response.date_next_payment + timedelta(days=1, hours=1),  # запас по времени 1 день и 1 час
            profile_id=response.profile_id
        )

        # учет операции
        await AsyncOrm.add_operation(user.tg_id, "AUTO_PAY", response.date_last_payment)
        logger.info(f"Пользователь с tg id {user.tg_id}, телефон {user.phone} автоматически оплатил подписку")
