import pytest

from unittest.mock import Mock

from sqlalchemy import select

from src.models.models import User
from tests.conftest import TestingSessionLocal


user_data = {
    "username": "kadulin",
    "email": "kadulin@gmail.com",
    "password": "password",
    # "is_verified": True,
    # "avatar": "https://res.cloudinary.com/dgknpebae/image/upload/c_fill,h_250,w_250/v1718230002/web21/kadulin%40gmail.com",
}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]

    assert "password" not in data
    # assert "avatar" in data

    # assert mock_send_email.called


def test_signup_repeat(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 409, response.text
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    data = response.json()
    print(f"data: {data}")
    assert data["detail"] == "Account already exists"


def test_not_confirm_login(client):
    response = client.post(
        "/api/auth/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )

    assert response.status_code == 401, response.text
    data = response.json()
    assert data.get("detail") == "Email not confirmed"


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).filter_by(email=user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.is_verified = True
            await session.commit()

    response = client.post(
        "/api/auth/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    print(f"{data=}")
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data

def test_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    print(f"{data=}")
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


# def test_login_user2(client, session, user):
#     print(f"{user=}")
#     current_user: User = (
#         session.query(User).filter(User.email == user.get("email")).first()
#     )
#     current_user.confirmed = True
#     session.commit()
#     print("!!!!! -----   1   ------ !!!!!")
#     response = client.post(
#         "/api/auth/login",
#         data={"username": user.get("email"), "password": user.get("password")},
#     )
#     assert response.status_code == 200, response.text
#     data = response.json()
#     assert data["token_type"] == "bearer"
