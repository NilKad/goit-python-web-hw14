import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from src.models.models import Base, User
from src.database.db import get_db
from src.services.auth import auth_service


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

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


@pytest.fixture(scope="module")
async def async_session(init_model_wrap):
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="module")
def client(async_session):
    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def user():
    return {
        "username": "kadulin",
        "email": "kadulin@example.com",
        "password": "22331144",
    }
