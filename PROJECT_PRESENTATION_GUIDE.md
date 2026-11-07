# StudyFlow: Project Guide for Presenting

## The idea in one minute

StudyFlow is an academic planner for university students. It puts courses, assignments, deadlines, and study sessions in one place. A student enters their tasks and the hours they are free to study. StudyFlow can then use AI to suggest a study schedule and help the student focus on urgent work. The goal is to make it easier to see what is coming up and plan time before deadlines arrive.

**A simple way to introduce it:**

> “StudyFlow helps students organize coursework and plan study time. It keeps their courses and deadlines together, then uses their availability and upcoming tasks to create a more manageable study plan.”

## How the project is put together

The project has two main parts that communicate over the internet:

1. **The frontend** is the part students see and click: the dashboard, courses, task list, calendar, and availability pages.
2. **The backend** is the part that handles requests, checks rules, works with the database, and asks the AI service for a schedule when needed.
3. **The database** saves account and planning information so it is still there the next time a student signs in.

The frontend sends a request to the backend when a student takes an action. For example, when they add a task, the backend checks the information, saves it in the database, and sends a response. The frontend then shows the saved task. The frontend does not connect directly to the database.

```text
Student
  ↓ uses
Frontend (the website)
  ↓ sends requests to
Backend API (rules and planning)
  ├── saves and reads information in → PostgreSQL database
  └── requests schedule suggestions from → Google Gemini AI
```

An **API** is the agreed way for the website and backend to ask each other for information. StudyFlow uses a REST API: requests use familiar web methods, such as reading a task or creating one, and addresses name things like `/api/v1/tasks` and `/api/v1/courses`.

## What the main tools do

| Tool | In everyday terms |
| --- | --- |
| **React** | Builds the pages and reusable screen parts, such as task cards and calendar views. |
| **TypeScript** | Adds checks to the frontend code to catch some mistakes while developers are writing it. |
| **Tailwind CSS** | Helps style the pages and adapt them to different screen sizes. |
| **FastAPI (Python)** | Runs the backend API, checks incoming information, and connects the website to the project’s data and planning logic. |
| **PostgreSQL** | Stores the students, courses, tasks, free-time slots, and study blocks in an organized database. |
| **SQLAlchemy** | Lets the Python backend read and change database records using Python code. |
| **Alembic** | Keeps track of changes to the database structure as the project develops. |
| **Google Gemini** | Receives task and availability details and returns a proposed study schedule in a structured format. |
| **Docker Compose** | Starts the backend and database together in a consistent development setup. |
| **Vite** | Starts the frontend during development and prepares it to be built for deployment. |
| **JWT bearer tokens** | Let the backend recognize a signed-in student on later requests without asking for the password each time. |
| **Telegram alerts (optional)** | Can notify the project team if monitoring detects a backend or AI problem. |

## What happens when a student uses it

1. The student registers or logs in. The backend checks their credentials and gives the frontend a sign-in token.
2. The student adds courses and tasks, including due dates and estimated effort. These are saved in PostgreSQL.
3. The student enters available and blocked study times. This tells StudyFlow when sessions could fit.
4. When the student asks for a schedule, the backend gathers their upcoming tasks and free time, then asks Gemini for a proposed plan.
5. The backend checks the proposed sessions and saves valid study blocks. The calendar and dashboard can then display them.
6. The student can update task progress or mark a study session complete. The website sends those changes to the backend to save.

AI provides a suggestion, while the application remains responsible for checking the result before it is saved. If there are too many tasks for the available hours, the plan can show an overload warning instead of pretending everything fits.

## How information is organized

Each student has their own courses and availability. A course can have several tasks, and a task can have study blocks scheduled for it. For example, a student’s “Biology 101” course could contain a lab report task, with two study sessions leading up to its due date. This structure connects a calendar session back to the task and course it belongs to.

The API checks that a student is signed in and only returns or changes that student’s records. This matters because course schedules and deadlines are personal. A student’s ID in a web address is not treated as permission to access someone else’s information.

## What to emphasize in a presentation

- **The problem:** students can lose track of deadlines spread across several courses and have trouble deciding when to study.
- **The solution:** one place to manage courses and tasks, plus a calendar that relates study time to deadlines.
- **The useful input:** the plan depends on both the tasks and the student’s actual available hours.
- **The role of AI:** AI helps propose a schedule; the application checks and stores the result.
- **The design:** the visible website, backend, and database have separate jobs, which makes each part easier to update.

If asked why the project uses separate frontend and backend parts, a simple answer is: “The frontend focuses on the student experience, while the backend handles saved data and rules. They communicate through the API.”

## A beginner's tour of the code

The repository has two main folders. `frontend/` contains the website code, and `backend/` contains the API and database code. When following a feature, it helps to trace it from the screen toward the database:

| Where to look | What you will find |
| --- | --- |
| `frontend/src/features/tasks/TasksPage.tsx` | The tasks screen: it displays the list and connects buttons and forms to task actions. |
| `frontend/src/features/tasks/api/tasks.ts` | The functions that load, add, edit, delete, or prioritize tasks. |
| `frontend/src/shared/api/client.ts` | The shared helper that sends requests to the backend and attaches the sign-in token. |
| `backend/app/api/v1/tasks.py` | The task API routes: the code that receives requests and decides what should happen. |
| `backend/app/schemas/planner.py` | Rules for the shape of incoming and outgoing data, such as which task fields are required. |
| `backend/app/models/task.py` | The task's database structure: its fields and links to a student, course, and study blocks. |
| `backend/app/services/scheduler.py` | The steps that prepare schedule information, check AI suggestions, and save study blocks. |

### Example: adding a task

When a student saves a task in the website, the task form calls the create-task function in `frontend/src/features/tasks/api/tasks.ts`. That function uses `apiClient` to send a `POST` request with the task information as JSON. The request is sent to `/api/v1/tasks` and includes the student's bearer token.

The route in `backend/app/api/v1/tasks.py` receives the request. FastAPI uses the `TaskCreate` schema from `planner.py` to check fields such as the title, due date, course ID, and estimated hours. The route also checks that the chosen course belongs to the signed-in student. It then creates a database task and commits it, which means it saves the change. The API returns the new task with a `201 Created` status, and the frontend refreshes its task list so the new item appears.

Here is the shape of the request in everyday terms:

```http
POST /api/v1/tasks
Authorization: Bearer <student token>
Content-Type: application/json

{"course_id": 7, "title": "Biology lab report", "due_date": "2026-11-12T23:59:00Z", "estimated_hours": 3, "weight_percent": 15}
```

The response includes the saved task and its database ID. That ID lets later requests refer to this one task, for example `/api/v1/tasks/42`.

### A few code terms you may hear

- A **route** or **endpoint** is an API address plus the code for handling it. For example, `@router.post("")` in the task router handles requests to create tasks.
- A **schema** is a shape-and-rules check for data. `TaskCreate` checks what the website may send; `TaskRead` describes task data the API may return.
- A **model** describes how data is stored in the database. The `Task` model has fields such as `title`, `due_date`, and `status`.
- A **query** is a request to find or change database rows. The task list query filters by the signed-in student's ID and can also filter by status or due date.
- A **hook** is a reusable frontend function. In `tasks.ts`, hooks such as `useTasks` load task data, while `useCreateTask` sends a create request and refreshes the screen data after success.
- **JSON** is a common text format for sending named values between the frontend and backend.

### What happens during AI scheduling

The schedule route asks the scheduler service to assemble the student's tasks and available time windows. The service sends the relevant information and instructions to Gemini. The AI returns proposed sessions in a defined data shape. The backend then checks that each session points to a real task, fits an available time window, and has sensible start and end times before saving it. This checking step is important: an AI suggestion is treated as input to validate, not as a database change that is automatically trusted.

## One detail to keep consistent

The current backend code is configured to use **Google Gemini** for AI scheduling. The project proposal still mentions **OpenAI GPT-4o-mini**, so those documents do not currently match. When presenting, describe the implementation as using Gemini unless the team changes the code or confirms that the proposal is the intended version.
