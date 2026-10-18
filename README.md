# inkwell-api

Blog REST API built with FastAPI, PostgreSQL, and JWT auth. Project 3 of a 15-project backend series.

## Features

- JWT authentication (register / login, bcrypt-hashed passwords)
- Posts with unique slugs, drafts vs published visibility, publish/unpublish
- Comments nested under posts
- Tags with many-to-many posts relationship, popular-tags ranking
- Pagination, filtering (tag, author), full-text-ish search via ILIKE
- Cover image uploads (JPEG/PNG/WebP, 5 MB limit), served statically
- Ownership rules: drafts visible to author only; edits/deletes restricted to owners; other users' private resources return 404 to avoid leaking existence
- Alembic migrations, pytest suite, GitHub Actions CI

## Quickstart

```bash
docker compose up -d          # start Postgres
alembic upgrade head          # run migrations
uvicorn app.main:app --reload # start API (http://localhost:8000)
```

Seed demo data:

```bash
python scripts/seed.py
```

Run tests (in-memory SQLite, no database needed):

```bash
pip install -e ".[dev]"
pytest -q
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://inkwell:inkwell@localhost:5432/inkwell` | Database connection |
| `SECRET_KEY` | `dev-only-secret-key-change-me-in-production` | JWT signing key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime |
| `UPLOAD_DIR` | `./uploads` | Cover image storage |
| `MAX_UPLOAD_SIZE_MB` | `5` | Upload size cap |

## API

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | – | Register (201, 409 on duplicate) |
| POST | `/auth/login` | – | Login with form fields, returns JWT |

### Posts

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/posts` | yes | Create post (draft by default) |
| GET | `/posts` | optional | List with `skip`, `limit`, `tag`, `author_id`, `q` |
| GET | `/posts/{slug}` | optional | Get one post |
| PATCH | `/posts/{slug}` | yes | Edit own post (title change regenerates slug) |
| DELETE | `/posts/{slug}` | yes | Delete own post |
| POST | `/posts/{slug}/publish` | yes | Publish own post |
| POST | `/posts/{slug}/unpublish` | yes | Unpublish own post |
| POST | `/posts/{slug}/cover` | yes | Upload cover image |

### Comments

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/posts/{slug}/comments` | yes | Comment on a post |
| GET | `/posts/{slug}/comments` | optional | List comments |
| PATCH | `/comments/{id}` | yes | Edit own comment |
| DELETE | `/comments/{id}` | yes | Delete own comment |

### Tags

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/tags` | – | List all tags |
| GET | `/tags/popular` | – | Top 10 tags by published post count |

### Ops

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/uploads/{file}` | Serve uploaded cover images |

## Example

```bash
TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -d "username=alice@example.com&password=secret123" | jq -r .access_token)

curl -s -X POST localhost:8000/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello Inkwell","body":"My first post","tag_names":["intro"]}' | jq .slug

curl -s -X POST localhost:8000/posts/hello-inkwell/publish \
  -H "Authorization: Bearer $TOKEN" | jq .published
```

## Design notes

- Slugs are generated from titles and made unique (`my-post`, `my-post-2`).
- Anonymous users see published posts only; signed-in users also see their own drafts.
- Requesting another user's private resource returns 404, not 403.
- Tests override the database dependency with in-memory SQLite, so CI needs no Postgres.
