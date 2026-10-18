def test_list_tags(client, auth_headers):
    client.post(
        "/posts",
        json={"title": "T1", "body": "b", "tag_names": ["python", "fastapi"]},
        headers=auth_headers,
    )
    tags = client.get("/tags").json()
    names = {t["name"] for t in tags}
    assert {"python", "fastapi"} <= names


def test_duplicate_tag_names_reuse_tag(client, auth_headers):
    client.post(
        "/posts", json={"title": "T1", "body": "b", "tag_names": ["Python"]},
        headers=auth_headers,
    )
    client.post(
        "/posts", json={"title": "T2", "body": "b", "tag_names": ["python"]},
        headers=auth_headers,
    )
    tags = client.get("/tags").json()
    python_tags = [t for t in tags if t["slug"] == "python"]
    assert len(python_tags) == 1


def test_popular_tags_counts_published_only(client, auth_headers):
    draft = client.post(
        "/posts", json={"title": "D", "body": "b", "tag_names": ["draft-tag"]},
        headers=auth_headers,
    ).json()["slug"]
    live = client.post(
        "/posts", json={"title": "L", "body": "b", "tag_names": ["live-tag"]},
        headers=auth_headers,
    ).json()["slug"]
    client.post(f"/posts/{live}/publish", headers=auth_headers)
    popular = {t["slug"]: t["post_count"] for t in client.get("/tags/popular").json()}
    assert popular.get("live-tag") == 1
    assert "draft-tag" not in popular


def test_filter_by_author(client, auth_headers, second_auth_headers):
    slug = client.post(
        "/posts", json={"title": "Mine", "body": "b"}, headers=auth_headers
    ).json()["slug"]
    client.post(f"/posts/{slug}/publish", headers=auth_headers)
    other = client.post(
        "/posts", json={"title": "Theirs", "body": "b"}, headers=second_auth_headers
    ).json()["slug"]
    client.post(f"/posts/{other}/publish", headers=second_auth_headers)
    me_id = client.get(f"/posts/{slug}").json()["author"]["id"]
    results = client.get(f"/posts?author_id={me_id}").json()
    assert len(results) == 1
    assert results[0]["title"] == "Mine"
