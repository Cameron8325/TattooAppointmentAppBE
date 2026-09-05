# Imaginarium studio API

Django and REST Framework for studio accounts, clients, appointments, approvals,
and completed-work billing. Local development uses `tattoo_app.settings.dev`;
existing production settings stay in `tattoo_app.settings.prod`.

## Run and validate

Install `requirements.txt`, configure `.env` from `.env.example`, then run
`python manage.py migrate` and `python manage.py runserver`.

Run the full suite against isolated in-memory storage:

```sh
python manage.py test --settings=tattoo_app.settings.test
```

Booking edits use one workflow for both update endpoints. A pending move holds
its original time until reviewed. Declining restores the complete prior booking,
including client, price and deposit details. Ordinary edits preserve completed
status. Studio fees are rounded to cents per session before totaling the report.

## Free public demo

`render.yaml` defines a separate free demo API. Its settings always use a
disposable SQLite database, never the studio's `DATABASE_URL`. Startup migrates
and seeds an empty database with fictional clients. A single worker handles
requests so demo SQLite writes are serialized. Set `SECRET_KEY` to a generated
secret and `FRONTEND_URL` to the exact public frontend origin.

The sample logins are `admin` and `mia.torres` (also `leo.nakamura` and
`ava.bennett`), using `DevSeed123!`. These identities are protected from login
changes and deletion in demo mode, and do not grant access to Django admin.
New demo team members can be managed normally.

Free Render instances sleep when idle. The first request may take about a
minute, and sample changes can reset when the service restarts. This is a demo,
not storage for real studio records. The frontend forwards `/api/*` on its own
origin to keep session and CSRF cookies working together.
