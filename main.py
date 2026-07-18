from fastapi import FastAPI

app = FastAPI()


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