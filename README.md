# StudyFlow — AI-Powered Academic Planner

Monorepo:

```text
academic-planner/
├── backend/    # FastAPI + PostgreSQL + Alembic
├── frontend/   # React + Tailwind + TypeScript
├── docs/       # API documentation
└── StudyFlow.postman_collection.json
```

## Run the backend (Docker)

```bash
cd backend
cp .env.example .env
docker compose up --build
```

- HTML Greeting: http://localhost:8000/api/v1/greeting
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json
- Health: http://localhost:8000/api/v1/health

Migrations are applied automatically on container start.

## Local development (without backend container)

```bash
cd backend
docker compose up -d db
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed_demo   # optional: seeds demo + RBAC test accounts
uvicorn app.main:app --reload
```

## Run the frontend

```bash
cd frontend
pnpm install
pnpm dev
```

## API & RBAC Overview

- Full API reference: [`docs/API.md`](docs/API.md) and [`StudyFlow.postman_collection.json`](StudyFlow.postman_collection.json).
- All JSON responses follow a standard envelope (`{ success, message, data, meta? }` and `{ success: false, error: { code, message, details? } }`).
- Seeded RBAC test accounts (`password123`):
  - **User A (`user`):** `usera@studyflow.edu`
  - **User B (`user`):** `userb@studyflow.edu`
  - **Admin (`admin`):** `admin@studyflow.edu`
- Endpoints support `GET`, `POST`, `PUT`, `PATCH`, and `DELETE` across `/courses`, `/tasks`, `/availability`, `/study-blocks`, and `/schedule`.
- Telegram alerts: set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`; without them alerts are only logged.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
PYTHONPATH=. pytest -q
```

## Contributors & Git Shortlog

See [`CONTRIBUTORS.md`](CONTRIBUTORS.md) for student IDs and team responsibilities:
- **Nargiz Bayramova:** Backend REST API, PostgreSQL schema & migrations, RBAC, error/response envelopes, and monitoring/Telegram alerts.
- **Maryam Aliyeva:** Frontend React/TypeScript UI/UX, interactive calendar & dashboard, and client state management.
- **Sumaya Gafarova:** Project proposal, requirements engineering, AI scheduling & prioritization logic, and system architecture.

```text
$ git shortlog -sn --all
    50  nargizbayramova
    22  Nargiz Bayramova
    17  maryamaliyeva7
    11  SumayaGafarova
```
