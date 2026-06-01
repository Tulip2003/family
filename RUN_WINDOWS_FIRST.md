# Windows install fix for Roomies Enterprise

Your install stopped at `psycopg2-binary==2.9.9` with:

```text
Error: pg_config executable not found.
```

Because that dependency failed, Flask was never installed. That is why later commands showed:

```text
'flask' is not recognized
ModuleNotFoundError: No module named 'flask'
```

This fixed package uses `psycopg[binary]` instead, which installs more smoothly on Windows and works with Neon PostgreSQL.

## Clean reinstall

Run these commands from the project folder:

```bat
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python scripts\create_env.py
python -m flask --app app reset-db
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Important

Use `python -m flask`, not only `flask`, on Windows. It avoids PATH problems.

## Neon URL

You can paste your Neon URL into `.env` as either:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/neondb?sslmode=require
```

or:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/neondb?sslmode=require
```

The app now automatically converts plain `postgresql://` to `postgresql+psycopg://`.
