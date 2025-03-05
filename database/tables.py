import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship


class Base(DeclarativeBase):
    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        """Relationships не используются в repr(), т.к. могут вести к неожиданным подгрузкам"""
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"


class User(Base):
    """Таблица для хранения пользователей"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str] = mapped_column(index=True, unique=True)
    username: Mapped[str] = mapped_column(nullable=True)
    firstname: Mapped[str] = mapped_column(nullable=True)
    lastname: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(index=True, nullable=True)

    subscription: Mapped[list["Subscription"]] = relationship(
        back_populates="user",
    )


class Subscription(Base):
    """Таблица с подписками пользователей"""
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    active: Mapped[bool] = mapped_column(default=False)
    start_date: Mapped[datetime.datetime] = mapped_column(nullable=True)
    expire_date: Mapped[datetime.datetime] = mapped_column(nullable=True)
    profile_id: Mapped[str] = mapped_column(nullable=True, default=None)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="subscription")


class Operation(Base):
    """Хранит действия пользователей подписки/отписки/покупки"""
    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str] = mapped_column(index=True)
    type: Mapped[str]
    date: Mapped[datetime.datetime]