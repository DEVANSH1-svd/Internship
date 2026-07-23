from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import init_db
app = FastAPI()

init_db()
class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Buy milk", "done": True},
]


@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.post("/tasks", status_code=201)
def create_task(new_task: TaskCreate):
    if len(new_task.title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    next_id = max(task["id"] for task in tasks) + 1
    task = {"id": next_id, "title": new_task.title, "done": False}
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: TaskUpdate):
    if len(updated_task.title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = updated_task.title
            task["done"] = updated_task.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")