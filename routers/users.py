import datetime
import os

from aiogram import Router, types
from aiogram.filters import Command

from database.orm import AsyncOrm
from database.schemas import UserAdd
from routers import messages as ms
from routers import keyboards as kb
from services import prodamus
from routers.utils import convert_date
from services.logger import logger

router = Router()


@router.callback_query(lambda c: c.data == "back_to_start")
@router.message(Command("start"))
async def start_handler(message: types.Message | types.CallbackQuery) -> None:
    """Старт бота и регистрация пользователя"""
    # проверка наличия пользователя
    tg_id = str(message.from_user.id)
    user = await AsyncOrm.get_user_by_tg_id(tg_id)

    # уже зарегистрирован
    if user:

        user_with_sub = await AsyncOrm.get_user_with_subscription_by_tg_id(tg_id)

        # подписка активна или неактивна, но еще не вышел оплаченный срок
        if user_with_sub.subscription[0].active or \
                (user_with_sub.subscription[0].expire_date is not None and
                 user_with_sub.subscription[0].expire_date.date() >= datetime.datetime.now().date()):

            msg = "<b>Меню участника канала «Ежедневное питание | Sheva Nutrition»:</b>"
            if type(message) == types.Message:
                await message.answer(msg, reply_markup=kb.main_menu_keyboard(sub_is_active=True).as_markup())
            else:
                await message.message.edit_text(msg, reply_markup=kb.main_menu_keyboard(sub_is_active=True).as_markup())

        # подписка неактивна
        else:
            # раньше была подписка
            if user.phone:
                msg = ms.welcome_message_second()
            # еще не было подписки
            else:
                msg = ms.get_welcome_message()

            if type(message) == types.Message:
                await message.answer(msg, reply_markup=kb.subscription_keyboard().as_markup())
            else:
                await message.message.edit_text(msg, reply_markup=kb.subscription_keyboard().as_markup())

    # регистрация
    else:
        msg = ms.get_welcome_message()
        # создание пользователя
        new_user = UserAdd(
            tg_id=str(message.from_user.id),
            username=message.from_user.username,
            firstname=message.from_user.first_name,
            lastname=message.from_user.last_name
        )
        user_id = await AsyncOrm.create_user(new_user)

        # создание неактивной подписки
        await AsyncOrm.create_subscription(user_id)
        await message.answer(msg, reply_markup=kb.subscription_keyboard().as_markup())


@router.message(Command("menu"))
@router.callback_query(lambda c: c.data == "main_menu")
async def main_menu(message: types.Message | types.CallbackQuery) -> None:
    """Главное меню"""
    msg = "<b>Меню участника канала «Ежедневное питание | Sheva Nutrition»:</b>"
    user = await AsyncOrm.get_user_with_subscription_by_tg_id(str(message.from_user.id))

    # подписка активна
    if user.subscription[0].active:
        sub_is_active = True

    # подписка неактивна, но срок еще не вышел
    elif user.subscription[0].expire_date is not None and \
        user.subscription[0].expire_date.date() >= datetime.datetime.now().date():
        sub_is_active = True

    # подписка неактивна
    else:
        sub_is_active = False

    if type(message) == types.Message:
        await message.answer(msg, reply_markup=kb.main_menu_keyboard(sub_is_active).as_markup())
    else:
        await message.message.edit_text(msg, reply_markup=kb.main_menu_keyboard(sub_is_active).as_markup())


@router.message(Command("podpiska"))
@router.callback_query(lambda c: c.data == "callback_podpiska")
async def podpiska_menu(message: types.Message | types.CallbackQuery) -> None:
    """Меню управления подпиской"""
    msg = "Своей подпиской можно управлять здесь:"

    # проверка активности подписки
    user = await AsyncOrm.get_user_with_subscription_by_tg_id(str(message.from_user.id))
    # активна
    if user.subscription[0].active:
        active_sub = True
    # неактивна, но оплаченный срок еще не вышел
    elif user.subscription[0].expire_date is not None and \
            user.subscription[0].expire_date.date() >= datetime.datetime.now().date():
        active_sub = None
    # неактивна
    else:
        active_sub = False

    if type(message) == types.Message:
        await message.answer(msg, reply_markup=kb.podpiska_menu_keyboard(active_sub, need_back_button=False).as_markup())
    else:
        await message.message.edit_text(msg, reply_markup=kb.podpiska_menu_keyboard(active_sub, need_back_button=True).as_markup())


@router.message(Command("status"))
@router.callback_query(lambda c: c.data == "callback_status")
async def check_status_handler(message: types.Message | types.CallbackQuery) -> None:
    """Проверка статуса подписки"""
    tg_id = str(message.from_user.id)
    user_with_sub = await AsyncOrm.get_user_with_subscription_by_tg_id(tg_id)

    is_active = user_with_sub.subscription[0].active
    expire_date = user_with_sub.subscription[0].expire_date

    msg = ms.get_status_message(is_active, expire_date)

    if type(message) == types.Message:
        await message.answer(msg)
    else:
        await message.message.edit_text(msg, reply_markup=kb.back_keyboard("callback_podpiska").as_markup())


@router.message(Command("oplata"))
@router.callback_query(lambda c: c.data == "subscribe")
async def create_subscription_handler(message: types.CallbackQuery | types.Message) -> None:
    """Оформление подписки"""
    user = await AsyncOrm.get_user_with_subscription_by_tg_id(str(message.from_user.id))

    # подписка активна или неактивна, но срок еще не вышел
    if user.subscription[0].active or (user.subscription[0].expire_date is not None and
                 user.subscription[0].expire_date.date() >= datetime.datetime.now().date()):

        if type(message) == types.Message:
            await message.answer(
                ms.subscribe_message(),
                reply_markup=kb.payment_keyboard(need_back_button=False, need_pay_link=False).as_markup()
            )
        else:
            await message.message.edit_text(
                ms.subscribe_message(),
                reply_markup=kb.payment_keyboard(need_back_button=True, need_pay_link=False).as_markup()
            )

    else:
        payment_link = prodamus.get_pay_link(message.from_user.id)

        if type(message) == types.Message:
            await message.answer(
                ms.subscribe_message(),
                reply_markup=kb.payment_keyboard(payment_link, need_back_button=False).as_markup()
            )
        else:
            await message.message.edit_text(
                ms.subscribe_message(),
                reply_markup=kb.payment_keyboard(payment_link).as_markup()
            )


@router.message(Command("otmena"))
@router.callback_query(lambda c: c.data == "callback_otmena")
async def cancel_subscription_handler(message: types.Message | types.CallbackQuery) -> None:
    """Начало отмены подписки"""
    # проверяем активность подписки
    user = await AsyncOrm.get_user_with_subscription_by_tg_id(str(message.from_user.id))

    # если активна
    if user.subscription[0].active:
        msg = "<b>Вы действительной хотите отменить подписку?</b>"

        if type(message) == types.Message:
            await message.answer(msg, reply_markup=kb.yes_no_keyboard(need_back_button=False).as_markup())
        else:
            await message.message.edit_text(msg, reply_markup=kb.yes_no_keyboard(need_back_button=True).as_markup())

    # если неактивна либо отменена, но еще не вышел срок
    else:
        # подписка отменена и срок не вышел
        if user.subscription[0].expire_date is not None and user.subscription[0].expire_date > datetime.datetime.now():
            msg = f"Ваша подписка уже отменена, вы сможете ее продлить после окончания оплаченного периода " \
                  f"<b>{convert_date(user.subscription[0].expire_date)}</b>"
        # подписка отменена и вышел срок
        else:
            msg = "Ваша подписка неактивна\n<i>Вы можете приобрести подписку с помощью команды /oplata</i>"

        if type(message) == types.Message:
            await message.answer(msg)
        else:
            await message.message.edit_text(msg, reply_markup=kb.back_keyboard("callback_podpiska").as_markup())


@router.callback_query(lambda c: c.data == "yes_otmena")
async def confirmation_unsubscribe(callback: types.CallbackQuery) -> None:
    """Отмена подписки"""
    tg_id = str(callback.from_user.id)

    # получение подписки
    user_with_sub = await AsyncOrm.get_user_with_subscription_by_tg_id(tg_id)
    subscription_id = user_with_sub.subscription[0].id

    profile_id = user_with_sub.subscription[0].profile_id
    if profile_id:
        try:
            profile_id = int(profile_id)
        except Exception as e:
            logger.error(f"Не удалось преобразовать profile_id в int пользователя tg_id: {user_with_sub.tg_id}, "
                         f"phone: {user_with_sub.phone}")

    # отмена подписки через API Prodamus
    response = prodamus.cancel_sub_by_user(user_with_sub.phone, profile_id)

    if response.status_code == 200:
        # отмена подписки в БД
        await AsyncOrm.deactivate_subscribe(subscription_id)

        msg = ms.get_cancel_subscribe_message(user_with_sub.subscription[0].expire_date)
        await callback.message.edit_text(msg)

        await AsyncOrm.add_operation(user_with_sub.tg_id, "UN_SUB", datetime.datetime.now())
        logger.info(f"Пользователь с tg id {tg_id} отменил подписку")

    else:
        await callback.message.edit_text("Произошла ошибка при обработке запроса. Повторите запрос позже.")
        logger.error(
            f"Ошибка при отмене подписки у пользователя с tg id {tg_id}\n"
            f"status code: {response.status_code} | {response.text}"
        )


@router.message(Command("vopros"))
@router.callback_query(lambda c: c.data == "callback_vopros")
async def vopros_handler(message: types.Message | types.CallbackQuery) -> None:
    """Задать вопрос"""
    msg = ms.get_vopros_message()

    if type(message) == types.Message:
        await message.answer(msg)
    else:
        await message.message.edit_text(msg, reply_markup=kb.back_keyboard("main_menu").as_markup())
