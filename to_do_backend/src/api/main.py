from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware

from src.schemas import Task, TaskCreate, TaskUpdate
from src.storage import create_task, delete_task, get_task, init_db, list_tasks, update_task

openapi_tags = [
    {"name": "Health", "description": "Service health and usage info."},
    {"name": "Tasks", "description": "CRUD operations for to-do tasks."},
]

app = FastAPI(
    title="To-Do API",
    description=(
        "REST API for a simple To-Do list application.\n\n"
        "Frontend is expected to call this backend on **http://localhost:3001**.\n"
        "Tasks are persisted in a local SQLite database file inside the backend container."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# Allow the React frontend container (and local preview) to call the API.
# Note: In preview environments, origins can vary; allowing localhost + wildcard simplifies DX.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    """Initialize the SQLite schema on application startup."""
    init_db()


@app.get("/", tags=["Health"], summary="Health check", operation_id="healthCheck")
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON object with a short status message.
    """
    return {"message": "Healthy"}


@app.get("/tasks", response_model=List[Task], tags=["Tasks"], summary="List tasks", operation_id="listTasks")
def http_list_tasks():
    """
    List all tasks.

    Returns:
        A JSON array of Task objects ordered newest-first.
    """
    return list_tasks()


@app.post("/tasks", response_model=Task, tags=["Tasks"], summary="Create task", operation_id="createTask")
def http_create_task(payload: TaskCreate):
    """
    Create a new task.

    Args:
        payload: TaskCreate payload (title required).

    Returns:
        The created Task.
    """
    return create_task(title=payload.title, description=payload.description or "")


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    tags=["Tasks"],
    summary="Get task by id",
    operation_id="getTask",
)
def http_get_task(
    task_id: int = Path(..., ge=1, description="Task id"),
):
    """
    Get a task by id.

    Args:
        task_id: Task identifier.

    Returns:
        The Task if found.

    Raises:
        404 if the task does not exist.
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    tags=["Tasks"],
    summary="Update task",
    operation_id="updateTask",
)
def http_update_task(
    payload: TaskUpdate,
    task_id: int = Path(..., ge=1, description="Task id"),
):
    """
    Update a task by id (full/partial update).

    Supports changing title, description and/or completed state in one request.

    Args:
        task_id: Task identifier.
        payload: TaskUpdate payload (all fields optional).

    Returns:
        The updated Task.

    Raises:
        404 if the task does not exist.
        400 if no fields were provided.
    """
    if payload.title is None and payload.description is None and payload.completed is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    updated = update_task(
        task_id,
        title=payload.title,
        description=payload.description,
        completed=payload.completed,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@app.delete(
    "/tasks/{task_id}",
    tags=["Tasks"],
    summary="Delete task",
    operation_id="deleteTask",
)
def http_delete_task(
    task_id: int = Path(..., ge=1, description="Task id"),
):
    """
    Delete a task by id.

    Args:
        task_id: Task identifier.

    Returns:
        JSON: { "deleted": true }

    Raises:
        404 if the task does not exist.
    """
    ok = delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True}
