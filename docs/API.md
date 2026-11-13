# StudyFlow REST API Documentation (v1)

Interactive docs are also available when running the backend:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **HTML Greeting:** `http://localhost:8000/api/v1/greeting`

---

## 1. Response Envelopes

### Success (Single Resource / Action)
```json
{
  "success": true,
  "message": "Task created successfully.",
  "data": { "...": "..." }
}
```

### Success (Paginated List)
```json
{
  "success": true,
  "message": "Tasks retrieved successfully.",
  "data": [ "..." ],
  "meta": {
    "total": 12,
    "page": 1,
    "perPage": 50
  }
}
```

### Success (Delete)
Returns `200 OK`:
```json
{
  "success": true,
  "message": "Task deleted successfully.",
  "data": null
}
```

### Error Envelope
All `4xx` and `5xx` errors return:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid or missing fields.",
    "details": [
      { "field": "title", "message": "String should have at least 3 characters" }
    ]
  }
}
```
- `details` is included only for validation errors (`400`).
- Internal exceptions and stack traces are never exposed.

---

## 2. Authentication & Role-Based Access Control (RBAC)

StudyFlow uses JWT bearer tokens backed by PostgreSQL (`users.role` is `"user"` or `"admin"`).

- **Obtain token:** `POST /api/v1/auth/login` (OAuth2 form: `username` = email, `password` = password). Returns top-level `access_token` and `token_type` for RFC 6749 / Swagger UI Authorize compatibility.
- **Pass token on protected routes:**
  ```http
  Authorization: Bearer <access_token>
  ```
- **Seeded demo accounts** (via `python -m scripts.seed_demo`, password `password123`):
  - **User A (`user`):** `usera@studyflow.edu` — manages only their own resources.
  - **User B (`user`):** `userb@studyflow.edu` — manages only their own resources.
  - **Admin (`admin`):** `admin@studyflow.edu` — lists, reads, updates, and deletes any user's resources.

### Why `403 Forbidden` vs `404 Not Found`
When an authenticated regular user requests an existing resource ID owned by a different user, StudyFlow returns **`403 Forbidden`** (`"You do not have permission to access this Task"`), clearly separating **permission denial (`403`)** from **non-existent resource IDs (`404 Not Found`)**.

---

## 3. Main Resource CRUD: Tasks (`/api/v1/tasks`)

### 3.1 `GET /api/v1/tasks` — List Tasks
- **Headers:** `Authorization: Bearer <token>` (Role: `user` sees own tasks; `admin` sees all tasks)
- **Query Params:**
  - `page` (int, default `1`, `>= 1`)
  - `perPage` (int, default `50`, `1..100`)
  - `course_id` (int, optional)
  - `user_id` (int, optional, admin only)
  - `semester` (str, optional)
  - `type` (`assignment | exam | quiz | project_milestone`, optional)
  - `status` (`pending | in_progress | completed`, optional)
  - `priority` (`low | medium | high`, optional)
  - `due_from`, `due_to` (ISO-8601 datetime with timezone, optional)
  - `q` (str, max 100 chars, case-insensitive title search)
- **Responses:** `200 OK` (`PaginatedResponse`), `400 Bad Request` (invalid query param), `401 Unauthorized`.

**Example Request:**
```http
GET /api/v1/tasks?page=1&perPage=10&status=pending
Authorization: Bearer <token>
```
**Example Response (`200 OK`):**
```json
{
  "success": true,
  "message": "Tasks retrieved successfully.",
  "data": [
    {
      "id": 1,
      "course_id": 1,
      "title": "Homework 1: REST API Design",
      "description": null,
      "type": "assignment",
      "status": "pending",
      "priority": "medium",
      "due_date": "2026-11-15T10:00:00Z",
      "estimated_hours": 2.0,
      "weight_percent": 10.0,
      "ai_priority_score": null,
      "priority_rank": null,
      "urgency_level": null,
      "ai_recommendation": null,
      "completed_at": null,
      "created_at": "2026-11-13T06:00:00Z",
      "updated_at": "2026-11-13T06:00:00Z"
    }
  ],
  "meta": { "total": 1, "page": 1, "perPage": 10 }
}
```

### 3.2 `GET /api/v1/tasks/{task_id}` — Get Task by ID
- **Headers:** `Authorization: Bearer <token>` (Role: owner or `admin`)
- **Path Param:** `task_id` (int)
- **Responses:** `200 OK`, `400 Bad Request` (non-integer ID), `401 Unauthorized`, `403 Forbidden` (owned by another user), `404 Not Found` (ID does not exist).

### 3.3 `POST /api/v1/tasks` — Create Task
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json` (Role: course owner or `admin`)
- **Validation Rules** (`extra="forbid"` — unknown fields rejected):
  - `course_id`: required `int > 0` (must exist and be accessible)
  - `title`: required `str`, trimmed, `3..200` chars
  - `due_date`: required timezone-aware ISO-8601 datetime
  - `description`: optional `str`, max `2000` chars
  - `type`: `assignment | exam | quiz | project_milestone` (default `assignment`)
  - `status`: `pending | in_progress | completed` (default `pending`)
  - `priority`: `low | medium | high` (default `medium`)
  - `estimated_hours`: `float`, `> 0` and `<= 1000` (default `1.0`)
  - `weight_percent`: `float`, `0..100` (default `0.0`)
- **Responses:** `201 Created`, `400 Bad Request` (`VALIDATION_ERROR`), `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (`course_id` missing).

**Example Request:**
```json
{
  "course_id": 1,
  "title": "Prepare API Demo",
  "due_date": "2026-11-20T23:59:00Z",
  "estimated_hours": 3.0,
  "weight_percent": 15.0,
  "priority": "high"
}
```
**Example Validation Error (`400 Bad Request`):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid or missing fields.",
    "details": [
      { "field": "title", "message": "String should have at least 3 characters" },
      { "field": "unknown_key", "message": "Extra inputs are not permitted" }
    ]
  }
}
```

### 3.4 `PUT /api/v1/tasks/{task_id}` (and `PATCH /api/v1/tasks/{task_id}`) — Update Task
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json` (Role: owner or `admin`)
- **`PUT`:** Full replacement — all required fields (`course_id`, `title`, `due_date`) must be supplied and pass creation validation.
- **`PATCH`:** Partial update — only provided fields are validated and updated (`extra="forbid"`).
- **Responses:** `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

### 3.5 `DELETE /api/v1/tasks/{task_id}` — Delete Task
- **Headers:** `Authorization: Bearer <token>` (Role: owner or `admin`)
- **Responses:** `200 OK` (`data: null`), `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

---

## 4. All Endpoints Summary

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/greeting` | Styled HTML overview, team roster, and endpoint list |
| `GET` | `/api/v1/health` | Service & PostgreSQL connectivity probe |
| `POST` | `/api/v1/auth/register` | Register a student account |
| `POST` | `/api/v1/auth/login` | Authenticate and receive JWT bearer token |
| `GET/PUT/PATCH` | `/api/v1/auth/me` | Read or update current user profile |
| `GET/POST` | `/api/v1/courses` | List (paginated) or create courses |
| `GET` | `/api/v1/courses/semesters` | List distinct semesters |
| `GET/PUT/PATCH/DELETE` | `/api/v1/courses/{course_id}` | Read, update, or delete a course (`409` on duplicate code+semester) |
| `GET/POST` | `/api/v1/tasks` | List/filter/search (paginated) or create tasks |
| `POST` | `/api/v1/tasks/prioritize` | AI-rank pending tasks |
| `GET/PUT/PATCH/DELETE` | `/api/v1/tasks/{task_id}` | Read, update, or delete a task |
| `GET/POST` | `/api/v1/availability` | List (paginated) or create weekly/date-specific slots |
| `GET/PUT/PATCH/DELETE` | `/api/v1/availability/{slot_id}` | Read, update, or delete an availability slot (`409` on overlap) |
| `GET/POST` | `/api/v1/study-blocks` | List (paginated) or create study blocks |
| `GET/PUT/PATCH/DELETE` | `/api/v1/study-blocks/{block_id}` | Read, update, or delete a study block |
| `GET` | `/api/v1/schedule` | Get current study schedule |
| `POST` | `/api/v1/schedule/generate` | Generate AI study schedule |
| `POST` | `/api/v1/schedule/rebalance` | Rebalance schedule around missed sessions |
| `PATCH` | `/api/v1/schedule/blocks/{block_id}/status` | Mark a block `planned`, `completed`, or `missed` |
| `GET` | `/api/v1/schedule/analytics` | Weekly workload & high-stress analytics |
| `GET` | `/api/v1/schedule/export.ics` | Export schedule & deadlines as RFC 5545 `.ics` |
