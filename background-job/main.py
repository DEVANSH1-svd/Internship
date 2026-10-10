import datetime
import logging

import inngest
import inngest.fast_api
from fastapi import FastAPI

app = FastAPI(title="Background Job API")

# The client is this app's identity in Inngest. It is also how we will send events.
inngest_client = inngest.Inngest(
    app_id="report-api",
    logger=logging.getLogger("uvicorn"),
)


@app.get("/health")
def health():
    return {"status": "ok"}


# A background function. It runs when an event named "test/hello" arrives.
@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context) -> str:
    # A durable sleep: Inngest remembers it, and no worker stays busy while it waits.
    await ctx.step.sleep("wait-five-seconds", datetime.timedelta(seconds=5))
    return "Hello from the background!"


# Adds the /api/inngest route that the Dev Server calls to run our functions.
inngest.fast_api.serve(app, inngest_client, [say_hello])