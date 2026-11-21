# Group 6 - StudyFlow

# Assignment 2 - Part 1: Conspectus

## 1. REST and Resources

A web API needs to be designed by using REST (Representational State Transfer). Anything the client uses, say StudyFlow lesson plan, task, or learning practice, is a resource. The HTTP method defines ways to use a resource, as the URL identifies it. In this case, the command `GET /api/v1/tasks/42` requests task 42 and provides details on its parameters.

URLs referencing resources rather than encoding commands are simpler to comprehend. The list of tasks visible to the registered student in StudyFlow is called `/api/v1/tasks`; one task inside that collection is identified as `/api/v1/tasks/42`. Because they represent a group of resources, collects typically are plural; each member is chosen by the identifier.

In our project - StudyFlow, `GET /api/v1/courses` to list courses and `DELETE /api/v1/study-blocks/18` to remove any study block are good deign alternatives. It wouldn't be right choice to use endpoints like `GET /api/v1/getAllCourses` or `POST /api/v1/deleteStudyBlock/18`. So, in this case, we don't need to add the action in the URL because the HTTP methods already tell us what we're doing. By concentrating on resources and ensuring that users only access their own data, the present API maintains things simple.

## 2. HTTP Methods

`GET` can simply read a view without requesting the server to change it. In StudyFlow, `GET /api/v1/tasks?status=pending` returns pending/open tasks. `POST` submits input data to a collection, and generally creating a new resource; `POST /api/v1/tasks` creates new task/assignment. `PUT` replaces any resource data with the representation sent by the client directly; for instance, `PUT /api/v1/tasks/42` can replace editable fields of a task completely. The project also uses (in initial version) `PATCH /api/v1/tasks/42` for partial edits, so that is the method a client must use. And finally, `DELETE /api/v1/tasks/42` is used to remove/delete that assignment/task.

Safe denotes the request is intended only to read data. But idempotent means repeating the same request/submission already has exact same impact like submitting it once. And a response can be differerent (for instance, 2nd detele attempt returns 'not found'), while the intended resource state remains deleted.

| Method   | Safe | Idempotent | Typical use                          |
| -------- | ---- | ---------- | ------------------------------------ |
| `GET`    | Yes  | Yes        | Read a task or task list             |
| `POST`   | No   | No         | Create a task or generate a schedule |
| `PUT`    | No   | Yes        | Replace a task representation        |
| `DELETE` | No   | Yes        | Remove a task                        |

`POST` is not idempotent because submitting create request twice can create 2 different outputs. If a client times out and retries without knowing if 1st attempt reached system, then th student could see a duplicate assignment/task. And clients should definitely avoid blindly retrying this kind of requests; APIs that need safe retries can add a specific idempotency mechanism.

## 3. HTTP Status Codes

Status codes give a meaning to the responses, and the response body can explain what happened.

- `200 OK`: the request with successful resulr. Using it when `GET /api/v1/tasks/42` returns an existing task.
- `201 Created`: the request created a resource. StudyFlow can return it after `POST /api/v1/courses` creates a course.
- `400 Bad Request`: the request cannot be processed as sent. For instance, Ssystem can return it when schedule generation receives an unknown time-zone name.
- `401 Unauthorized`: missing/invalid authentication. A request to list tasks with an expired bearer token should receive this response.
- `403 Forbidden`: user(student) is authenticated, however role does not allow the intented operation. For instance, any student attempting to use a hypothetical administrator-only account management endpoint would receive it.
- `404 Not Found`: the requested resource is unavailable at that URL, appropriate for a missing task ID.
- `409 Conflict`: the intented request conflicts with current/existing data. Creating a course with a course code and semester combination that already exists for the student should return it.

`401` asks the client to authenticate/ provide valid user credentials.
`403` means the server recognizes the caller but denies that caller permission.
`404` is returned in system for another student's resource ID so that it does not reveal whether the resource exists.

## 4. API Responses and Errors

The frontend, individually, cannot identify which input has to be corrected or what assignment was submitted based only on status code. By bypassing this check, any user could do unauthorized modifications such as - reading or removing other user's personal data by altering an ID in a URL.
And React client allows users to view data as well as handle issues without making assumptions because of well-tructured JSON response, which offers elements a known layout. Any error description should explain the issue in exact language that the user can resolve. Local file locations, or database messages shouldn't be sent by the API since they can reveal details about the implementation and mislead users. StudyFlow initially offers field-level errors for validation and surrounds mistakes with a description, error/issue and status codes.

Sample of success response from `GET /api/v1/tasks/42`:

```json
{
  "id": 42,
  "title": "Calculus problem set",
  "status": "pending",
  "due_date": "2026-11-12T23:59:00Z"
}
```

And sample evalidation error when a task title is missing (StudyFlow's validation responses use `422`):

```json
{
  "detail": "title: Field required",
  "error_code": "VALIDATION_ERROR",
  "status_code": 422,
  "field_errors": [{ "field": "title", "message": "Field required" }]
}
```

## 5. Authentication and Authorization

Authorisation validates the actions of a user who is already logged in, while authentication confirms who is submitting request. In StudyFlow it provides a token upon login. On protected requests, such as `Authorisation: Bearer <token>`, the frontend transmits it in the `Authorisation` header. The token is checked and the active user is determined by the backend.

Instead of creating a unique rule for each individual, role-based access control (RBAC) allocates rights to roles. A typical student will manage their individual classes, assignments, estimated study time, and schedule in dashboard. A system administrator shouldn't misuse personal student data, however they may oversee existing accounts and deal with technical or system-level problems (if required). The present version does not yet create a particular administrator role, however it does provide user authentication and ownership checks.

All queries and updates must be limited to the resources of the logged-in user. By bypassing this review, any user could do unauthorized modifications such as - reading or removing other student's personal study / schedule data by altering an ID in a URL. Before generating a task, system verifies if connected courses belong to the right user and verifies ownership when retrieving or maybe removing a single item. And this ensures preventing IDs from functioning as authorization on their own.

## 6. Sources Used

- [MDN — HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)
- [MDN — HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [Microsoft — Web API design best practices](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design)
- [Google Cloud — RESTful API design: What about errors?](https://cloud.google.com/blog/products/api-management/restful-api-design-what-about-errors)
