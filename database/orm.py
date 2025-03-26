import datetime
from typing import List

import pytz
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from database.database import async_engine, async_session_factory
from database.tables import Base
from database import schemas
from database import tables


class AsyncOrm:

    @staticmethod
    async def create_user(new_user: schemas.UserAdd) -> int:
        """Создание пользователя и подписки в базе данных"""
        async with async_session_factory() as session:
            user = tables.User(**new_user.dict())
            session.add(user)

            await session.flush()
            user_id = user.id
            await session.commit()
            return user_id

    @staticmethod
    async def get_user_by_tg_id(tg_id: str) -> schemas.User | None:
        """Получение пользователя по tg id"""
        async with async_session_factory() as session:
            query = select(tables.User).where(tables.User.tg_id == tg_id)

            result = await session.execute(query)
            row = result.scalars().first()
            if row:
                user = schemas.User.model_validate(row, from_attributes=True)
                return user
            else:
                return

    @staticmethod
    async def create_subscription(user_id: int) -> None:
        """Создание подписки пользователю"""
        async with async_session_factory() as session:
            subscription = tables.Subscription(
                user_id=user_id
            )
            session.add(subscription)
            await session.flush()
            await session.commit()

    @staticmethod
    async def get_user_with_subscription_by_tg_id(tg_id: str) -> schemas.UserRel:
        """Получение подписки и связанного пользователя по tg id"""
        async with async_session_factory() as session:
            query = select(tables.User)\
                .where(tables.User.tg_id == tg_id)\
                .options(joinedload(tables.User.subscription))

            result = await session.execute(query)
            row = result.scalars().first()
            user = schemas.UserRel.model_validate(row, from_attributes=True)

            return user

    @staticmethod
    async def deactivate_subscribe(subscription_id: int) -> None:
        """Отмена подписки"""
        async with async_session_factory() as session:
            query = update(tables.Subscription)\
                .where(tables.Subscription.id == subscription_id)\
                .values(active=False)

            await session.execute(query)
            await session.flush()
            await session.commit()

    @staticmethod
    async def update_subscribe(subscription_id: int,
                               start_date: datetime.datetime,
                               expire_date: datetime.datetime,
                               profile_id: str) -> None:
        """Оформление подписки"""
        async with async_session_factory() as session:
            query = update(tables.Subscription) \
                .where(tables.Subscription.id == subscription_id) \
                .values(active=True, start_date=start_date, expire_date=expire_date, profile_id=profile_id)

            await session.execute(query)
            await session.flush()
            await session.commit()

    # @staticmethod
    # async def get_subscription(subscription_id: int) -> schemas.Subscription | None:
    #     """Оформление подписки"""
    #     async with async_session_factory() as session:
    #         query = select(tables.Subscription).where(tables.Subscription.id == subscription_id)
    #
    #         result = await session.execute(query)
    #         row = result.scalars().first()
    #         if row:
    #             subscription = schemas.Subscription.model_validate(row, from_attributes=True)
    #             return subscription
    #         else:
    #             return

    @staticmethod
    async def get_all_users() -> List[schemas.User]:
        """Получение всех пользователей"""
        async with async_session_factory() as session:
            query = select(tables.User)

            result = await session.execute(query)
            rows = result.scalars().all()
            users = [schemas.User.model_validate(row, from_attributes=True) for row in rows]

            return users

    @staticmethod
    async def get_subscription_by_user_id(user_id: int) -> schemas.Subscription:
        """Получение подписки по id пользователя"""
        async with async_session_factory() as session:
            query = select(tables.Subscription).where(tables.Subscription.user_id == user_id)

            result = await session.execute(query)
            row = result.scalars().first()
            subscription = schemas.Subscription.model_validate(row, from_attributes=True)

            return subscription

    @staticmethod
    async def remove_expire_date(subscription_id: int) -> None:
        """Замена expire_date на null"""
        async with async_session_factory() as session:
            query = update(tables.Subscription) \
                .where(tables.Subscription.id == subscription_id) \
                .values(expire_date=None)

            await session.execute(query)
            await session.flush()
            await session.commit()

    @staticmethod
    async def add_operation(tg_id: str, operation_type: str, date: datetime.datetime) -> None:
        """Создание операции пользователя
            BUY_SUB - покупка подписки
            AUTO_PAY - автопродление подпсики
            UN_SUB - отмена подписки пользователем
            AUTO_UN_SUB - отмена подписки автоматически (при неоплате)
        """
        async with async_session_factory() as session:
            operation = tables.Operation(
                tg_id=tg_id,
                type=operation_type,
                date=date
            )
            session.add(operation)

            await session.flush()
            await session.commit()

    @staticmethod
    async def add_user_phone(user_id: int, phone_number: str) -> None:
        """Запись телефона пользователю"""
        async with async_session_factory() as session:
            query = update(tables.User) \
                .where(tables.User.id == user_id) \
                .values(phone=phone_number)

            await session.execute(query)
            await session.flush()
            await session.commit()

    @staticmethod
    async def deactivate_subscription(user_id: int) -> None:
        """Деактивация подписки у пользователя"""
        async with async_session_factory() as session:
            query = update(tables.Subscription) \
                .where(tables.Subscription.user_id == user_id) \
                .values(active=False, expire_date=None)

            await session.execute(query)
            await session.flush()
            await session.commit()

    @staticmethod
    async def get_all_tg_ids() -> list[str]:
        """Получение списка tg_id всех пользователей"""
        async with async_session_factory() as session:
            query = select(tables.User.tg_id)

            result = await session.execute(query)
            rows = result.scalars().all()

            return rows

    @staticmethod
    async def get_inactive_users_tg_ids() -> list[str]:
        """Получение списка tg_id всех пользователей с неактивной подпиской"""
        async with async_session_factory() as session:
            query = select(tables.Subscription.user_id).where(tables.Subscription.active == False)
            result = await session.execute(query)
            users_ids = result.scalars().all()

            query = select(tables.User.tg_id).filter(tables.User.id.in_(users_ids))
            result = await session.execute(query)
            users_tg_ids = result.scalars().all()

            return users_tg_ids

    @staticmethod
    async def get_unsub_tg_ids() -> list[str]:
        """Получение списка tg_id отписавшихся пользователей"""
        async with async_session_factory() as session:
            query = select(tables.Operation.tg_id).where(tables.Operation.type == "UN_SUB")

            result = await session.execute(query)
            rows = result.scalars().all()

            return list(set(rows))