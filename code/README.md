# Public Procurement Support System

Web application supporting municipal public procurement.

## Setup and Running

1. Install dependencies and create the virtual environment:
   ```bash
   uv sync
   ```
2. Run the development server:
   ```bash
   uv run python manage.py runserver
   ```

## Testing

Run the test suite:
```bash
uv run --env-file .env pytest
```

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
