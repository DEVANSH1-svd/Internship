from fastapi import FastAPI

# Create the FastAPI application instance.
# This object is the core of your server — every route attaches to it.
app = FastAPI()


@app.get("/")
def read_root():
    """A simple hello message, so we know the server is alive."""
    return {"message": "Hello, this is my Task API!"}