from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import init_db, get_all_tasks, get_task_by_id, create_task_db, update_task_db, delete_task_db

app = FastAPI()
init_db()


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return get_all_tasks()


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201)
def create_task(new_task: TaskCreate):
    if len(new_task.title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    return create_task_db(new_task.title, done=False)


@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: TaskUpdate):
    if len(updated_task.title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    task = update_task_db(task_id, updated_task.title, updated_task.done)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    deleted = delete_task_db(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")