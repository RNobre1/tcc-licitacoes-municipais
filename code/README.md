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
uv run pytest
```

Check code style and formatting:
```bash
uv run ruff check .
uv run ruff format --check .
```

## Domain Glossary

Domain concepts in code follow standard English identifiers mapped to Brazilian procurement law. Refer to [`GLOSSARY.md`](GLOSSARY.md) as the single source for domain naming conventions.
