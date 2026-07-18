from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class TaskCreate(BaseModel):
    title: str


# In-memory "database" — a plain Python list of dictionaries.
# This data lives only in RAM and resets every time the server restarts.
tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Buy milk", "done": True},
]


@app.get("/")
def read_root():
    """Describes the API: its name, version, and available endpoints."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health")
def health_check():
    """Used by monitoring tools to confirm the server is alive."""
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    """Returns every task currently stored."""
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Returns a single task by its id, or 404 if it doesn't exist."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.post("/tasks", status_code=201)
def create_task(new_task: TaskCreate):
    """Creates a new task. Title must not be missing or empty."""
    if len(new_task.title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    next_id = max(task["id"] for task in tasks) + 1
    task = {"id": next_id, "title": new_task.title, "done": False}
    tasks.append(task)
    return task