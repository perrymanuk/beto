# Radbot Task API

A simple, read-only API for accessing Radbot task and project data stored in a PostgreSQL database. This API supports visualization of the task list and is containerized for deployment.

## Features

- Read-only API endpoints for tasks and projects
- Filtering tasks by status and project
- Containerized with Docker and docker-compose
- Built with FastAPI and SQLAlchemy

## Technology Stack

- **Backend Framework:** FastAPI (Python)
- **Database ORM:** SQLAlchemy (Python)
- **Database:** PostgreSQL
- **Containerization:** Docker

## Setup and Installation

### Prerequisites

- Docker and docker-compose
- Python 3.10+ (for local development)

### Using Docker Compose

1. Clone this repository
2. Create a `.env` file based on `.env.example`
3. Start the containers:

```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`.

### Local Development

1. Clone this repository
2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example` and configure your database connection

5. Run the application:

```bash
uvicorn app.main:app --reload
```

## API Endpoints

- **`GET /api/v1/projects`**
  - Retrieve a list of all projects

- **`GET /api/v1/projects/{project_id}`**
  - Retrieve details for a specific project

- **`GET /api/v1/projects/{project_id}/tasks`**
  - Retrieve a list of tasks for a specific project
  - Optional query parameters:
    - `status`: Filter by status (e.g., 'backlog', 'inprogress', 'done')

- **`GET /api/v1/tasks`**
  - Retrieve a list of all tasks across all projects
  - Optional query parameters:
    - `status`: Filter by status
    - `project_id`: Filter by project UUID

- **`GET /api/v1/tasks/{task_id}`**
  - Retrieve details for a specific task

## Documentation

Once the server is running, you can access the auto-generated API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database Schema

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
- `project_id`: UUID (Primary Key)
- `name`: Text
- `created_at`: Timestamp

## Future Considerations

- Add authentication/authorization
- Implement write endpoints (POST, PUT, PATCH, DELETE)
- Integrate with frontend visualizations
- Add more advanced filtering and sorting options