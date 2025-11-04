import logging
from fastapi import FastAPI, Request
import uvicorn

from app.core.lifespan import lifespan
from app.core.webhook_handler import handle_webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(request: Request):
    return await handle_webhook(request, app.state)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
