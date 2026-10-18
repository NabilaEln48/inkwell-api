def make_post(client, headers, title="Hello World", body="Body text", tags=None):
    payload = {"title": title, "body": body, "tag_names": tags or []}
    response = client.post("/posts", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_create_post_generates_slug(client, auth_headers):
    post = make_post(client, auth_headers, title="My First Post")
    assert post["slug"] == "my-first-post"
    assert post["published"] is False
    assert post["author"]["email"] == "tester@example.com"


def test_create_post_requires_auth(client):
    response = client.post("/posts", json={"title": "x", "body": "y"})
    assert response.status_code == 401


def test_duplicate_titles_get_unique_slugs(client, auth_headers):
    first = make_post(client, auth_headers, title="Same Title")
    second = make_post(client, auth_headers, title="Same Title")
    assert first["slug"] == "same-title"
    assert second["slug"] == "same-title-2"


def test_draft_invisible_to_anonymous(client, auth_headers):
    post = make_post(client, auth_headers)
    response = client.get(f"/posts/{post['slug']}")
    assert response.status_code == 404


def test_draft_visible_to_author(client, auth_headers):
    post = make_post(client, auth_headers)
    response = client.get(f"/posts/{post['slug']}", headers=auth_headers)
    assert response.status_code == 200


def test_draft_invisible_to_other_user(client, auth_headers, second_auth_headers):
    post = make_post(client, auth_headers)
    response = client.get(f"/posts/{post['slug']}", headers=second_auth_headers)
    assert response.status_code == 404


def test_publish_makes_post_public(client, auth_headers):
    post = make_post(client, auth_headers)
    response = client.post(f"/posts/{post['slug']}/publish", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["published"] is True
    public = client.get(f"/posts/{post['slug']}")
    assert public.status_code == 200


def test_unpublish_hides_post_again(client, auth_headers):
    post = make_post(client, auth_headers)
    client.post(f"/posts/{post['slug']}/publish", headers=auth_headers)
    client.post(f"/posts/{post['slug']}/unpublish", headers=auth_headers)
    assert client.get(f"/posts/{post['slug']}").status_code == 404


def test_author_can_update_own_post(client, auth_headers):
    post = make_post(client, auth_headers, title="Old Title")
    response = client.patch(
        f"/posts/{post['slug']}", json={"title": "New Title"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["slug"] == "new-title"


def test_other_user_cannot_update_post(client, auth_headers, second_auth_headers):
    post = make_post(client, auth_headers)
    client.post(f"/posts/{post['slug']}/publish", headers=auth_headers)
    response = client.patch(
        f"/posts/{post['slug']}", json={"title": "Hacked"}, headers=second_auth_headers
    )
    assert response.status_code == 404


def test_author_can_delete_own_post(client, auth_headers):
    post = make_post(client, auth_headers)
    response = client.delete(f"/posts/{post['slug']}", headers=auth_headers)
    assert response.status_code == 204
    assert client.get(f"/posts/{post['slug']}", headers=auth_headers).status_code == 404


def test_other_user_cannot_delete_post(client, auth_headers, second_auth_headers):
    post = make_post(client, auth_headers)
    client.post(f"/posts/{post['slug']}/publish", headers=auth_headers)
    response = client.delete(f"/posts/{post['slug']}", headers=second_auth_headers)
    assert response.status_code == 404


def test_list_posts_pagination(client, auth_headers):
    for i in range(5):
        slug = make_post(client, auth_headers, title=f"Post {i}")["slug"]
        client.post(f"/posts/{slug}/publish", headers=auth_headers)
    first_page = client.get("/posts?limit=2").json()
    second_page = client.get("/posts?limit=2&skip=2").json()
    assert len(first_page) == 2
    assert len(second_page) == 2
    assert first_page[0]["slug"] != second_page[0]["slug"]


def test_list_posts_excludes_drafts_for_anonymous(client, auth_headers):
    make_post(client, auth_headers, title="Draft Post")
    published = make_post(client, auth_headers, title="Live Post")
    client.post(f"/posts/{published['slug']}/publish", headers=auth_headers)
    posts = client.get("/posts").json()
    assert len(posts) == 1
    assert posts[0]["title"] == "Live Post"


def test_search_by_title(client, auth_headers):
    slug = make_post(client, auth_headers, title="FastAPI Tutorial")["slug"]
    client.post(f"/posts/{slug}/publish", headers=auth_headers)
    other = make_post(client, auth_headers, title="Cooking Recipes")["slug"]
    client.post(f"/posts/{other}/publish", headers=auth_headers)
    results = client.get("/posts?q=fastapi").json()
    assert len(results) == 1
    assert results[0]["title"] == "FastAPI Tutorial"


def test_filter_by_tag(client, auth_headers):
    slug = make_post(client, auth_headers, title="Tagged", tags=["python"])["slug"]
    client.post(f"/posts/{slug}/publish", headers=auth_headers)
    other = make_post(client, auth_headers, title="Untagged")["slug"]
    client.post(f"/posts/{other}/publish", headers=auth_headers)
    results = client.get("/posts?tag=python").json()
    assert len(results) == 1
    assert results[0]["title"] == "Tagged"


def test_tags_attached_on_create(client, auth_headers):
    post = make_post(client, auth_headers, tags=["Python", "Web"])
    names = {t["name"] for t in post["tags"]}
    assert names == {"Python", "Web"}


def test_post_includes_comment_count(client, auth_headers):
    post = make_post(client, auth_headers)
    client.post(f"/posts/{post['slug']}/publish", headers=auth_headers)
    client.post(
        f"/posts/{post['slug']}/comments",
        json={"body": "Nice post"},
        headers=auth_headers,
    )
    fetched = client.get(f"/posts/{post['slug']}").json()
    assert fetched["comment_count"] == 1
