import datetime

import aiogram
from database.orm import AsyncOrm
from services.channel import kick_user_from_channel


async def check_subscriptions_status(bot: aiogram.Bot) -> None:
    """Выполняется каждый час"""
    await check_sub_status(bot)


async def kick_inactive_users(bot: aiogram.Bot) -> None:
    """Выполняется каждый день"""
    await kick_users_with_not_active_sub(bot)


async def check_sub_status(bot: aiogram.Bot) -> None:
    """Проверяет активна ли подписка"""
    users = await AsyncOrm.get_all_users()

    for user in users:
        subscription = await AsyncOrm.get_subscription_by_user_id(user.id)
        if subscription.active:
            if subscription.expire_date < datetime.datetime.now():  # запас по времени 1 день
                await AsyncOrm.deactivate_subscribe(subscription.id)

                # оповещение пользователя
                try:
                    msg = f"Срок подписки истек!\n\nВы можете оформить подписку заново с помощью команды /status"
                    await bot.send_message(user.tg_id, msg)
                except:
                    pass


async def kick_users_with_not_active_sub(bot: aiogram.Bot) -> None:
    """Выгоняем из канала пользователей, у которых неактивная подписка"""
    users = await AsyncOrm.get_all_users()

    for user in users:
        subscription = await AsyncOrm.get_subscription_by_user_id(user.id)

        if subscription.expire_date is not None and subscription.expire_date < datetime.datetime.now() \
                and subscription.active is False:
            # обнуляем дату expire_date
            await AsyncOrm.remove_expire_date(subscription.id)

            # выгоняем из канала
            try:
                await kick_user_from_channel(int(user.tg_id), bot)

                # уведомляем пользователя
                msg = f"Вы удалены из канала"
                await bot.send_message(user.tg_id, msg)

            except Exception as e:
                print(e)
