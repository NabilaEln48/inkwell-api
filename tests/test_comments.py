def make_published_post(client, headers, title="Post"):
    response = client.post(
        "/posts", json={"title": title, "body": "body"}, headers=headers
    )
    slug = response.json()["slug"]
    client.post(f"/posts/{slug}/publish", headers=headers)
    return slug


def test_create_comment(client, auth_headers):
    slug = make_published_post(client, auth_headers)
    response = client.post(
        f"/posts/{slug}/comments", json={"body": "Great read"}, headers=auth_headers
    )
    assert response.status_code == 201
    body = response.json()
    assert body["body"] == "Great read"
    assert body["author"]["email"] == "tester@example.com"


def test_create_comment_requires_auth(client, auth_headers):
    slug = make_published_post(client, auth_headers)
    response = client.post(f"/posts/{slug}/comments", json={"body": "hi"})
    assert response.status_code == 401


def test_cannot_comment_on_draft_as_stranger(client, auth_headers, second_auth_headers):
    response = client.post(
        "/posts", json={"title": "Draft", "body": "b"}, headers=auth_headers
    )
    slug = response.json()["slug"]
    denied = client.post(
        f"/posts/{slug}/comments", json={"body": "hi"}, headers=second_auth_headers
    )
    assert denied.status_code == 404


def test_list_comments(client, auth_headers):
    slug = make_published_post(client, auth_headers)
    client.post(
        f"/posts/{slug}/comments", json={"body": "first"}, headers=auth_headers
    )
    client.post(
        f"/posts/{slug}/comments", json={"body": "second"}, headers=auth_headers
    )
    comments = client.get(f"/posts/{slug}/comments").json()
    assert [c["body"] for c in comments] == ["first", "second"]


def test_author_can_edit_own_comment(client, auth_headers):
    slug = make_published_post(client, auth_headers)
    comment_id = (
        client.post(
            f"/posts/{slug}/comments", json={"body": "typo"}, headers=auth_headers
        ).json()["id"]
    )
    response = client.patch(
        f"/comments/{comment_id}", json={"body": "fixed"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["body"] == "fixed"


def test_other_user_cannot_edit_comment(client, auth_headers, second_auth_headers):
    slug = make_published_post(client, auth_headers)
    comment_id = (
        client.post(
            f"/posts/{slug}/comments", json={"body": "mine"}, headers=auth_headers
        ).json()["id"]
    )
    response = client.patch(
        f"/comments/{comment_id}", json={"body": "hacked"}, headers=second_auth_headers
    )
    assert response.status_code == 404


def test_author_can_delete_own_comment(client, auth_headers):
    slug = make_published_post(client, auth_headers)
    comment_id = (
        client.post(
            f"/posts/{slug}/comments", json={"body": "bye"}, headers=auth_headers
        ).json()["id"]
    )
    response = client.delete(f"/comments/{comment_id}", headers=auth_headers)
    assert response.status_code == 204
    assert client.get(f"/posts/{slug}/comments").json() == []
