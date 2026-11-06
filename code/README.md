# Public Procurement Support System

Web application supporting municipal public procurement.

## Setup and Running

1. Install dependencies and create the virtual environment:
   ```bash
   uv sync
   ```
2. Create your local environment file from the example:
   ```bash
   cp .env.example .env
   ```
   For local development, set `DEBUG=True` in `.env`, so that the development server serves the static files. Outside development, replace `SECRET_KEY` with a generated key:
   ```bash
   uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. Run the development server:
   ```bash
   uv run --env-file .env python manage.py runserver
   ```

## Local Services

PostgreSQL 18.6 and Qdrant v1.20.0 run in containers defined in `compose.yaml`, bound to `127.0.0.1` only: PostgreSQL on port 5433 and Qdrant on port 6333.

```bash
make up    # starts both services and waits until they are healthy; requires .env
make down  # stops them; the data volumes are kept
uv run --env-file .env python manage.py migrate
```

The prototype screens run without these services: they read demo data from memory and keep screening decisions in a signed-cookie session. The ingestion commands and the integration tests need them.

## Public Data Ingestion

Fetch one window of procurement data from the public PNCP API, then measure it:

```bash
uv run --env-file .env python manage.py fetch_pncp --start 2026-10-26 --end 2026-10-30 --uf PA --modality 6
uv run --env-file .env python manage.py measure_sample --start 2026-10-26 --end 2026-10-30
```

- `fetch_pncp` stores every API page whole, as a `RawRecord`. It retries server errors and timeouts with exponential backoff, checks the item count against the API's own count, and writes each walk all or nothing. `--uf` defaults to `PA` and `--modality` to `6`, electronic reverse auction.
- `measure_sample` prints a deterministic report on the fetched window: counts, volume per day, missing fields, median description length and distinct units. Running it twice gives the same text.

Fetched data is real and stays in the local database. It is never committed.

## Testing

Run the test suite:
```bash
uv run --env-file .env pytest
```

The default run skips the tests marked `integration`, which need the local services. To include them, start the services first:
```bash
make up
uv run --env-file .env pytest -m ""
```

The integration tests share one test database, so two runs at the same time break each other. Run them one at a time.

Check code style and formatting:
```bash
uv run ruff check .
uv run ruff format --check .
```

## Frontend Layout

The project vendors the class-based build of [`@picocss/pico@2.0.6`](https://picocss.com/) at `static/vendor/pico-2.0.6/pico.min.css`, alongside its MIT license. The stylesheet's SHA-256 is `dd5fd5591afd81ee21dcc117ad85c014dc3f1f19dc2d7b7d101ea0acc29274c2`.

The project vendors [`htmx.org@2.0.4`](https://htmx.org/) at `static/vendor/htmx-2.0.4/htmx.min.js`, alongside its 0BSD license. The script's SHA-256 is `e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447`.

The selection criterion was a self-contained stylesheet with no CDN dependency, rather than simply avoiding a frontend build step. The federal government design system (`@govbr-ds/core`) can load without a build step, but its intended appearance depends on Rawline fonts and Font Awesome assets loaded from a CDN. Vendoring those assets would make govbr-ds a viable option later.

## Domain Glossary

Domain concepts in code follow standard English identifiers mapped to Brazilian procurement law. Refer to [`GLOSSARY.md`](GLOSSARY.md) as the single source for domain naming conventions.
