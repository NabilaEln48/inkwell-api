import io

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def make_post(client, headers):
    response = client.post(
        "/posts", json={"title": "Cover Post", "body": "b"}, headers=headers
    )
    return response.json()["slug"]


def test_upload_cover_image(client, auth_headers):
    slug = make_post(client, auth_headers)
    response = client.post(
        f"/posts/{slug}/cover",
        files={"file": ("cover.png", io.BytesIO(PNG_BYTES), "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cover_image_url"] is not None
    assert body["cover_image_url"].startswith("/uploads/")


def test_reject_non_image_upload(client, auth_headers):
    slug = make_post(client, auth_headers)
    response = client.post(
        f"/posts/{slug}/cover",
        files={"file": ("evil.txt", io.BytesIO(b"not an image"), "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 415


def test_reject_oversized_upload(client, auth_headers):
    slug = make_post(client, auth_headers)
    big = io.BytesIO(b"\x89PNG" + b"0" * (6 * 1024 * 1024))
    response = client.post(
        f"/posts/{slug}/cover",
        files={"file": ("big.png", big, "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 413


def test_other_user_cannot_upload_cover(client, auth_headers, second_auth_headers):
    slug = make_post(client, auth_headers)
    response = client.post(
        f"/posts/{slug}/cover",
        files={"file": ("cover.png", io.BytesIO(PNG_BYTES), "image/png")},
        headers=second_auth_headers,
    )
    assert response.status_code == 404


def test_uploaded_file_is_served(client, auth_headers):
    slug = make_post(client, auth_headers)
    url = client.post(
        f"/posts/{slug}/cover",
        files={"file": ("cover.png", io.BytesIO(PNG_BYTES), "image/png")},
        headers=auth_headers,
    ).json()["cover_image_url"]
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
