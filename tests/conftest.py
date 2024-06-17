import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

# from requests import session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


from main import app
from src.models.models import Base, User
from src.database.db import get_db
from src.services.auth import auth_service

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user = {
    "username": "deadpool",
    "email": "deadpool@example.com",
    "password": "password",
}


@pytest.fixture(scope="module", autouse=True)
def init_moddel_wrap():
    async def init_model():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            password_hash = auth_service.get_password_hash(test_user["password"])
            current_user = User(
                username=test_user["username"],
                email=test_user["email"],
                password=password_hash,
                is_verified=True,
                avatar="https://res.cloudinary.com/dgknpebae/image/upload/c_fill,h_250,w_250/v1718230002/web21/kadulin%40gmail.com",
                role="admin",
            )
            session.add(current_user)
            await session.commit()

    asyncio.run(init_model())


# TODO test need delete
@pytest.fixture(scope="module")
def client():
    # Dependency override

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        except Exception as err:
            print(err)
            await session.rollback()
            raise err
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)
