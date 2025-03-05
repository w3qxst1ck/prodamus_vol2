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
    async def create_tables():
        """Создание таблиц"""
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

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
    async def disactivate_subscribe(subscription_id: int) -> None:
        """Отмена подписки"""
        async with async_session_factory() as session:
            query = update(tables.Subscription)\
                .where(tables.Subscription.id == subscription_id)\
                .values(active=False)

            await session.execute(query)
            await session.flush()
            await session.commit()

    @staticmethod
    async def update_subscribe(subscription_id: int) -> None:
        """Оформление подписки"""
        async with async_session_factory() as session:
            start_date = (datetime.datetime.now(tz=pytz.timezone("Europe/Moscow"))).date()
            expire_date = (datetime.datetime.now(tz=pytz.timezone("Europe/Moscow")) + datetime.timedelta(days=30)).date()

            query = update(tables.Subscription) \
                .where(tables.Subscription.id == subscription_id) \
                .values(active=True, start_date=start_date, expire_date=expire_date)

            await session.execute(query)
            await session.flush()
            await session.commit()

    @staticmethod
    async def get_subscription(subscription_id: int) -> schemas.Subscription | None:
        """Оформление подписки"""
        async with async_session_factory() as session:
            query = select(tables.Subscription).where(tables.Subscription.id == subscription_id)

            result = await session.execute(query)
            row = result.scalars().first()
            if row:
                subscription = schemas.Subscription.model_validate(row, from_attributes=True)
                return subscription
            else:
                return

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
        """Создание операции пользователя BUY_SUB/AUTO_PAY/UN_SUB"""
        async with async_session_factory() as session:
            operation = tables.Operation(
                tg_id=tg_id,
                type=operation_type,
                date=date
            )
            session.add(operation)

            await session.flush()
            await session.commit()