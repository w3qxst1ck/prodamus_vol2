import aiogram
from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from routers import keyboards as kb
from routers.fsm_states import SendMessagesFSM
from database.orm import AsyncOrm

router = Router()


@router.callback_query(lambda c: c.data == "menu_administration")
async def admin_menu(callback: types.CallbackQuery) -> None:
    """Меню администратора"""
    msg = "Панель администратора"
    await callback.message.edit_text(msg, reply_markup=kb.admin_keyboard().as_markup())


@router.callback_query(lambda c: c.data == "notify_users")
async def choose_users(callback: types.CallbackQuery) -> None:
    """Выбор списка пользователей для отправки сообщения"""
    msg = "\"<b>Всем пользователям</b>\" - рассылка сообщения всем пользователям в боте\n\n" \
          "\"<b>Польз. без подписки</b>\" - рассылка сообщения пользователям с неактивной подпиской " \
          "(отмененной или еще не оформленной подпиской)\n\n" \
          "\"<b>Отменившим подписку</b>\" - рассылка сообщения пользователям, которые отменили подписку"

    await callback.message.edit_text(msg, reply_markup=kb.admin_users_group().as_markup())


@router.callback_query(lambda c: c.data.split("_")[0] == "users-group")
async def notify_users(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Подготовка сообщения для пользователей"""
    user_group = callback.data.split("_")[1]

    await state.set_state(SendMessagesFSM.text)
    await state.update_data(user_group=user_group)

    msg = "Отправьте в чат сообщение, которое вы бы хотели разослать "
    if user_group == "all":
        msg += "всем пользователям"
    elif user_group == "inactive":
        msg += "пользователям, еще не оформившим или отменившим подписку"
    else:
        msg += "пользователям, которые отменили подписку"

    prev_mess = await callback.message.edit_text(msg, reply_markup=kb.skip_or_cancel_keyboard().as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.message(SendMessagesFSM.text)
@router.callback_query(SendMessagesFSM.text, lambda c: c.data == "button_skip")
async def get_message_for_users(message: types.Message, state: FSMContext) -> None:
    """Получение сообщения для пользователей и переход в SendMessagesFSM.media"""
    # редактирование предыдущего сообщения
    data = await state.get_data()
    prev_mess = data["prev_mess"]
    try:
        await prev_mess.edit_text(prev_mess.text)
    except Exception:
        pass

    # сохраняем сообщение для пользователей
    if type(message) == types.Message:
        await state.update_data(text=message.text)
    # если пропускаем
    else:
        await state.update_data(text=None)

    await state.set_state(SendMessagesFSM.media)

    if type(message) == types.Message:
        prev_mess = await message.answer(
            "Отправьте 1 фото или видео, которое хотите приложить к сообщению",
            reply_markup=kb.skip_or_cancel_keyboard().as_markup()
        )
    else:
        prev_mess = await message.message.answer(
            "Отправьте 1 фото или видео, которое хотите приложить к сообщению",
            reply_markup=kb.skip_or_cancel_keyboard().as_markup()
        )

    await state.update_data(prev_mess=prev_mess)


@router.message(SendMessagesFSM.media, F.photo)
@router.message(SendMessagesFSM.media, F.video)
@router.callback_query(SendMessagesFSM.media, lambda c: c.data == "button_skip")
async def send_messages_to_users(message: types.Message | types.CallbackQuery, state: FSMContext, bot: aiogram.Bot) -> None:
    """Рассылка сообщения для пользователей"""
    data = await state.get_data()
    photo_id = None
    video_id = None

    # редактирование предыдущего сообщения
    prev_mess = data["prev_mess"]
    try:
        await prev_mess.edit_text(prev_mess.text)
    except Exception:
        pass

    if type(message) == types.Message:

        # получаем фото если есть
        if message.photo:
            photo_id = message.photo[-1].file_id

        # получаем видео если есть
        if message.video:
            video_id = message.video.file_id

    # сообщение об осуществлении отправки
    wait_text = "⏳ Выполняется рассылка..."
    if type(message) == types.Message:
        wait_msg = await message.answer(wait_text)
    else:
        wait_msg = await message.message.answer(wait_text)

    await state.clear()

    msg = data["text"]

    # получаем list tg_id пользователей для рассылки
    user_group = data["user_group"]
    users_ids = await get_user_group_ids(user_group)

    # рассылаем сообщения
    for tg_id in users_ids:
        try:

            # если все поля пустые
            if msg is None and photo_id is None and video_id is None:
                await wait_msg.edit_text("Невозможно отправить пустое сообщение")
                return

            # отправка без фото и видео
            if type(message) == types.CallbackQuery:
                await bot.send_message(tg_id, msg)

            # отправка с фото
            elif photo_id:
                await bot.send_photo(chat_id=tg_id, photo=photo_id, caption=msg)

            # отправка с видео
            elif video_id:
                await bot.send_video(chat_id=tg_id, video=video_id, caption=msg)

        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю при оповещении {user_group} {tg_id}: {e}")

    await wait_msg.edit_text("✅ Пользователи оповещены")


@router.callback_query(lambda callback: callback.data == "button_cancel", StateFilter("*"))
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    """Cancel FSM and delete last message"""
    await state.clear()
    await callback.message.answer("<b>Действие отменено</b> ❌")
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass


async def get_user_group_ids(user_group: str) -> list[str]:
    """Возвращает список tg_id пользователей"""
    if user_group == "all":
        users_ids = await AsyncOrm.get_all_tg_ids()
    elif user_group == "inactive":
        users_ids = await AsyncOrm.get_inactive_users_tg_ids()
    else:
        users_ids = await AsyncOrm.get_unsub_tg_ids()

    return users_ids
