# Task API Design Document

## Objective

Design and implement a simple, read-only API for accessing Radbot task and project data stored in a PostgreSQL database. This API will initially support visualization of the task list and will be containerized for deployment.

## Technology Stack

- **Backend Framework:** FastAPI (Python)
- **Database ORM:** SQLAlchemy (Python)
- **Database:** PostgreSQL
- **Containerization:** Docker

## Database Schema (Based on current understanding)

### Task
- `task_id`: UUID (Primary Key)
- `project_id`: UUID (Foreign Key to Project)
- `description`: Text
- `status`: Text (e.g., 'backlog', 'inprogress', 'done')
- `category`: Text (Nullable)
- `origin`: Text (Nullable)
- `created_at`: Timestamp
- `related_info`: JSON (Nullable)

### Project
- `id`: UUID (Primary Key)
- `name`: Text
- `created_at`: Timestamp

## API Endpoints (Read-Only for Visualization)

- **`GET /projects`**
  - **Description:** Retrieve a list of all projects.
  - **Response:** `List[Project]`

- **`GET /projects/{project_id}`**
  - **Description:** Retrieve details for a specific project.
  - **Parameters:** `project_id` (UUID)
  - **Response:** `Project`

- **`GET /tasks`**
  - **Description:** Retrieve a list of all tasks across all projects.
  - **Query Parameters:**
    - `status`: Filter by status (e.g., 'backlog', 'inprogress', 'done')
    - `project_id`: Filter by project UUID
  - **Response:** `List[Task]` (Tasks should include project name)

- **`GET /tasks/{task_id}`**
  - **Description:** Retrieve details for a specific task.
  - **Parameters:** `task_id` (UUID)
  - **Response:** `Task`

- **`GET /projects/{project_id}/tasks`**
  - **Description:** Retrieve a list of tasks for a specific project.
  - **Parameters:** `project_id` (UUID)
  - **Query Parameters:**
    - `status`: Filter by status
  - **Response:** `List[Task]`

## Implementation Notes

- Use SQLAlchemy models to map to PostgreSQL tables.
- Configure database connection using environment variables.
- Implement FastAPI routes for each endpoint.
- Utilize Pydantic models for request/response data validation and serialization.
- Include logic to join tasks with projects to retrieve project names for task listings.
- Build a Dockerfile for containerization.
- Initial version is read-only; functionality for creating, updating, or deleting tasks/projects can be added later.

## Future Considerations

- Add authentication/authorization if exposing outside local network.
- Implement write endpoints (POST, PUT, PATCH, DELETE).
- Integrate with the future agent interface frontend.
- Explore more advanced filtering and sorting options.
