from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from settings import settings


async_engine = create_async_engine(
    url=settings.db.DATABASE_URL,
    echo=False,
)

async_session_factory = async_sessionmaker(async_engine, autocommit=False)
