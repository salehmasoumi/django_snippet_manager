# Code Snippet Manager

Save, manage, and share code snippets with syntax highlighting, tags,
favorites, search/filtering, and a REST API.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # edit if needed (defaults work for local dev)

python manage.py migrate        # also seeds Python/Django/JS/HTML/CSS/C++/SQL/Bash
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

## Tests

```bash
python manage.py test
```

## Production notes

- Set `DB_ENGINE=postgresql` (plus `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`)
  in `.env` to switch from SQLite to Postgres with no code changes.
- Set `DEBUG=False` and run `python manage.py collectstatic` before deploying;
  WhiteNoise serves static files in production.
- Generate a real `SECRET_KEY` for production — never reuse the dev default.

## API

Browsable API at `/api/v1/` (session auth). Endpoints: `snippets/`, `languages/`,
`tags/`, `favorites/`. Private snippets are only visible to their owner, in the
web UI and the API alike.

## Roadmap

Version history (`SnippetVersion` per edit) is planned as a post-MVP addition;
see `ARCHITECTURE.md` for how the app boundaries were kept ready for it.
