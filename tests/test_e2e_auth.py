import pytest

from unittest.mock import Mock

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


# def test_signup_repeat(client, monkeypatch):
#     mock_send_email = Mock()
#     monkeypatch.setattr("src.services.email.send_email", mock_send_email)
#     response = client.post("/api/auth/signup", json=user_data)
#     assert response.status_code == 409, response.text
#     print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
#     data = response.json()
#     print(f"data: {data}")
#     assert data["detail"] == "Account already exists"


# def test_not_confirm_login(client):
#     response = client.post(
#         "/api/auth/login",
#         data={"username": user_data["email"], "password": user_data["password"]},
#     )
#     assert response.status_code == 401, response.text
#     data = response.json()
#     assert data["detail"] == "Email not confirmed"
