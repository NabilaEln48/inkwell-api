def test_register_returns_201(client):
    response = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "secret123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "hashed_password" not in body
    assert "password" not in body


def test_register_duplicate_email_returns_409(client, auth_headers):
    response = client.post(
        "/auth/register",
        json={"email": "tester@example.com", "password": "secret123"},
    )
    assert response.status_code == 409


def test_login_returns_jwt(client, auth_headers):
    response = client.post(
        "/auth/login",
        data={"username": "tester@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 0


def test_login_wrong_password_returns_401(client, auth_headers):
    response = client.post(
        "/auth/login",
        data={"username": "tester@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
