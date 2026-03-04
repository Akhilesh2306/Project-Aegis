# Import External Libraries
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Import Internal Packages
from config.settings import get_settings

# Get Settings
settings = get_settings()

# Create Async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db_session() -> AsyncSession:  # type: ignore
    async with AsyncSessionFactory() as session:
        yield session  # type: ignore
