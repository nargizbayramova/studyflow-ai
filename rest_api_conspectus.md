# REST API Conspectus

## 1. REST and Resources

REST (Representational State Transfer) is a way to structure a web API. A resource is something the client works with, such as a StudyFlow course, assignment, or study block. The URL identifies the resource, while the HTTP method says what to do with it. For example, `GET /api/v1/tasks/42` asks for task 42 and returns the data about details of task 42.

URLs are easier to understand when they name resources (in kebap case) instead of encoding commands (in cammel case). In StudyFlow, `/api/v1/tasks` is the collection of tasks available to the signed-in student. `/api/v1/tasks/42` identifies one task in that collection. Collections are usually plural because they represent a set of resources; the identifier selects one member.

Good designs for my project are `GET /api/v1/courses` to list my courses and `DELETE /api/v1/study-blocks/18` to remove one study block. Using endpoints like `GET /api/v1/getAllCourses` or `POST /api/v1/deleteStudyBlock/18` wouldn't be the best approach. The HTTP methods already tell us what action we're performing, so there's no need to include it in the URL. The current API keeps things cleaner by focusing on resources and making sure users only access their own data.

## 2. HTTP Methods

`GET` just reads a representation without asking the server to change it. In StudyFlow, `GET /api/v1/tasks?status=pending` retrieves pending tasks. `POST` submits data to a collection, commonly creating a new resource; `POST /api/v1/tasks` creates an assignment. `PUT` replaces a resource with the representation sent by the client; for example, `PUT /api/v1/tasks/42` could replace all editable fields of one task. The current project uses `PATCH /api/v1/tasks/42` for partial edits, so that is the method a client should use today. `DELETE /api/v1/tasks/42` removes that task.

Safe means the request is intended only to read data. Idempotent means repeating the same request has the same effect as sending it once. A response may differ (for example, a second delete can return not found), while the intended resource state remains deleted.

| Method   | Safe | Idempotent | Typical use                          |
| -------- | ---- | ---------- | ------------------------------------ |
| `GET`    | Yes  | Yes        | Read a task or task list             |
| `POST`   | No   | No         | Create a task or generate a schedule |
| `PUT`    | No   | Yes        | Replace a task representation        |
| `DELETE` | No   | Yes        | Remove a task                        |

`POST` is not idempotent because sending a create request twice can create two separate tasks. If a client times out and retries without knowing whether the first request reached StudyFlow, the student could see a duplicate assignment. Clients should avoid blindly retrying such requests; APIs that need safe retries can add a specific idempotency mechanism.

## 3. HTTP Status Codes

Status codes give a meaning to the responses, and the response body can explain what happened.

- `200 OK`: the request succeeded and has a result. Use it when `GET /api/v1/tasks/42` returns an existing task.
- `201 Created`: the request created a resource. StudyFlow can return it after `POST /api/v1/courses` creates a course.
- `400 Bad Request`: the request cannot be processed as sent. For example, StudyFlow can return it when schedule generation receives an unknown time-zone name.
- `401 Unauthorized`: authentication is missing or invalid. A request to list tasks with an expired bearer token should receive this response.
- `403 Forbidden`: the user is authenticated, but their role does not allow the requested operation. For example, an ordinary student trying to use a hypothetical administrator-only account management endpoint would receive it.
- `404 Not Found`: the requested resource is unavailable at that URL. It is appropriate for a missing task ID.
- `409 Conflict`: the request conflicts with current data. Creating a course with a course code and semester combination that already exists for the student should return it.

`401` asks the client to authenticate or provide valid credentials. `403` means the server recognizes the caller but denies that caller permission. StudyFlow currently returns `404` for another student's resource ID so that it does not reveal whether the resource exists.

## 4. API Responses and Errors

A status code alone does not tell the frontend what task was returned or which input needs correction. A structured JSON response gives fields a predictable shape, so the React client can display data and handle errors without guessing. Error details should name the problem in terms the student can fix. The API should not send stack traces, raw database messages, or internal file paths: these confuse users and can expose implementation details. StudyFlow already wraps errors with a detail, an error code, and a status code, and includes field-level errors for validation.

Example success response from `GET /api/v1/tasks/42`:

```json
{
  "id": 42,
  "title": "Calculus problem set",
  "status": "pending",
  "due_date": "2026-11-12T23:59:00Z"
}
```

Example validation error when a task title is missing (StudyFlow's validation responses use `422`):

```json
{
  "detail": "title: Field required",
  "error_code": "VALIDATION_ERROR",
  "status_code": 422,
  "field_errors": [{ "field": "title", "message": "Field required" }]
}
```

## 5. Authentication and Authorization

Authentication checks who is making a request; authorization checks what that signed-in person may do. After login, StudyFlow returns a bearer token. The frontend sends it in the `Authorization` header on protected requests, for example `Authorization: Bearer <token>`. The backend validates the token and identifies the current user.

Role-based access control (RBAC) assigns permissions to roles instead of making a separate rule for every person. In StudyFlow, a regular student should manage their own courses, tasks, study availability, and schedule. An administrator could manage user accounts and handle platform-level support issues, but should not casually read private academic details. The current prototype has student authentication and ownership checks; it does not yet define a separate administrator role.

Every query and update must be restricted to the signed-in user's resources. Without that check, changing an ID in a URL could let one student view, edit, or delete another student's deadlines and schedule. StudyFlow checks ownership when it fetches or deletes an individual resource and checks that linked courses belong to the student before creating a task. This keeps IDs from acting as permission by themselves.

## 6. Sources Used

- [MDN — HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)
- [MDN — HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [Microsoft — Web API design best practices](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design)
- [Google Cloud — RESTful API design: What about errors?](https://cloud.google.com/blog/products/api-management/restful-api-design-what-about-errors)
