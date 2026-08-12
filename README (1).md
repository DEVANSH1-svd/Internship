# Task API

A CRUD REST API for managing to-do tasks, built with FastAPI and backed by a real PostgreSQL database — containerized end-to-end with Docker.

This project evolved across three assignments, each swapping the storage layer while the API itself stayed the same:
- **A1** — tasks stored in memory (a Python list, lost on restart)
- **A2** — tasks stored in a SQLite file
- **A3 (this stage)** — tasks stored in a real Postgres database, running in its own container, with the whole stack (app + database) started via a single `docker compose up` command

The service and route logic never changed shape across this swap — only one file, `db.py` (the repository), was replaced. That's the architecture proving itself: storage is just an implementation detail behind a stable interface.

## Running it

**Requirements:** Docker Desktop installed and running.

1. Clone this repo and move into the project folder:
   ```bash
   git clone https://github.com/DEVANSH1-svd/Internship.git
   cd Internship/todo-api
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   (The default values work out of the box for local development — no changes needed unless you want a different password.)

3. Start the whole stack — API and database together, in one command:
   ```bash
   docker compose up --build
   ```

4. The API is now running at `http://localhost:8000`. Interactive docs are available at `http://localhost:8000/docs`.

On first startup, the `tasks` table is created automatically and seeded with 3 example tasks. Restarting the stack (`docker compose down` then `docker compose up`) will **not** duplicate the seed data or lose existing rows — the database lives in a Docker volume that persists independently of the containers.

## Environment variables

See `.env.example` for the required variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string. When running via `docker compose`, the app container reaches the database container using the service name `db` (not `localhost`) — this is already configured correctly in `compose.yaml`. |

## Endpoints

| Method | Path | Description | Success | Error |
|---|---|---|---|---|
| GET | `/` | API info | `200` | — |
| GET | `/health` | Health check | `200` | — |
| GET | `/tasks` | List all tasks | `200` | — |
| GET | `/tasks/{id}` | Get a single task by id | `200` | `404` if not found |
| POST | `/tasks` | Create a new task | `201` | `400` if title is empty |
| PUT | `/tasks/{id}` | Update a task's title/done status | `200` | `400` empty title, `404` not found |
| DELETE | `/tasks/{id}` | Delete a task | `204` | `404` if not found |

## Example request

```
$ curl -i http://localhost:8000/tasks

HTTP/1.1 200 OK
content-type: application/json

[{"id":1,"title":"Learn FastAPI","done":false},{"id":2,"title":"Build a CRUD API","done":false},{"id":3,"title":"Buy milk","done":true}]
```

## Database screenshot

<!-- Add your own screenshot here — see instructions below -->
![Database screenshot](db-screenshot.png)

*To generate this: run `docker exec -it <db-container-name> psql -U postgres -d tasks -c "\dt"` and `-c "SELECT * FROM tasks;"`, screenshot the terminal output, and save it as `db-screenshot.png` in this folder.*

## Architecture notes

All database logic lives in `db.py` — the repository module. `main.py` (routes) has no knowledge of SQL, connection strings, or Postgres specifically; it only calls functions like `get_all_tasks()` or `create_task_db(title, done)`. This separation is what allowed the storage engine to change from an in-memory list, to SQLite, to Postgres, without ever touching a route handler or changing an endpoint's request/response shape.

All queries use parameterized placeholders (`%s`) rather than string interpolation, to prevent SQL injection.

## Persistence, proven

To confirm data survives a full stack teardown (not just an app restart):
1. Created a task via `POST /tasks`
2. Ran `docker compose down` (removes both containers entirely)
3. Ran `docker compose up` again
4. Confirmed via `GET /tasks` that the created task was still present

This works because the Postgres data directory is mounted to a named Docker volume (`taskdata`), which exists independently of the container's lifecycle.

## Future improvements

- Add a `/health` check that also pings the database (`SELECT 1`) and reports `db: "ok"`
- Add an index on the `done` column and benchmark with `EXPLAIN ANALYZE`
- Add Redis to the compose stack for caching (planned for a later assignment)
- Multi-stage Dockerfile to slim the final image size
- Move to a layered architecture (routes / services / repository as separate modules)
