from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db import init_db, get_all_tasks, get_task_by_id, create_task_db, update_task_db, delete_task_db
from auth.supabase_client import supabase
import os
from pydantic import BaseModel, ValidationError
from llm.schema import EnrichRequest, EnrichResponse
from llm.stub import get_stub_response
from llm.client import call_model, call_model_for_repair, PROMPT_VERSION
from llm.parse import try_parse_json
from llm.quarantine import log_quarantine

app = FastAPI()
security = HTTPBearer()

init_db()
print("Server running and connected to Supabase")


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool

class AuthCredentials(BaseModel):
    email: str
    password: str

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/auth/signup", status_code=201)
def signup(credentials: AuthCredentials):
    if len(credentials.email.strip()) == 0 or len(credentials.password.strip()) == 0:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
        return {"user": result.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login", status_code=200)
def login(credentials: AuthCredentials):
    if len(credentials.email.strip()) == 0 or len(credentials.password.strip()) == 0:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        return {
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid login credentials")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Reusable dependency: extracts and verifies the Bearer token.
    Also registers the Bearer security scheme with FastAPI's OpenAPI docs,
    so /docs shows a padlock icon and an Authorize button for protected routes."""
    token = credentials.credentials

    try:
        result = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return result.user


@app.post("/auth/logout", status_code=204)
def logout(user = Depends(get_current_user)):
    supabase.auth.sign_out()
    return


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


@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
def protected_profile(user = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }


@app.get("/protected/dashboard")
def protected_dashboard(user = Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {user.email}!"}


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.post("/enrich", response_model=EnrichResponse)
def enrich(request: EnrichRequest):
    if os.getenv("LLM_STUB") == "1":
        return get_stub_response()

    input_data = request.model_dump()
    raw_text = call_model(input_data)

    parsed, parse_error = try_parse_json(raw_text)
    validation_error = None

    if parsed is not None:
        try:
            return EnrichResponse.model_validate(parsed)
        except ValidationError as e:
            validation_error = str(e)
    else:
        validation_error = parse_error

    # First attempt failed - repair once
    repaired_text = call_model_for_repair(input_data, raw_text, validation_error)
    repaired_parsed, repair_parse_error = try_parse_json(repaired_text)

    if repaired_parsed is not None:
        try:
            return EnrichResponse.model_validate(repaired_parsed)
        except ValidationError as e:
            log_quarantine(input_data, repaired_text, str(e), PROMPT_VERSION)
            raise HTTPException(status_code=422, detail="Model output failed validation after repair attempt")

    log_quarantine(input_data, repaired_text, repair_parse_error, PROMPT_VERSION)
    raise HTTPException(status_code=422, detail="Model output could not be parsed after repair attempt")


