from fastapi import FastAPI, Request
from loguru import logger
from dotenv import load_dotenv
import os

from logic.sync_logic import sync_all_leads_to_tasks, sync_tasks_to_leads
from utils.logger import logger as _configured_logger  # noqa: F401

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

app = FastAPI(title="Lead-Task Sync Webhook Server")


def _validate_secret(req: Request) -> bool:
    """Very simple shared-secret validator (optional)."""
    if not WEBHOOK_SECRET:
        return True
    header = req.headers.get("x-webhook-secret") or req.headers.get("X-Webhook-Secret")
    return header == WEBHOOK_SECRET


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/webhook/airtable")
async def airtable_webhook(request: Request) -> dict:
    if not _validate_secret(request):
        logger.warning("Invalid webhook secret on /webhook/airtable")
        return {"status": "forbidden"}

    payload = await request.json()
    logger.info(f"Received Airtable webhook: {str(payload)[:300]}")
    # For simplicity, we do not parse the payload deeply; we just trigger a targeted sync.
    sync_all_leads_to_tasks()
    return {"status": "ok"}


@app.post("/webhook/trello")
async def trello_webhook(request: Request) -> dict:
    if not _validate_secret(request):
        logger.warning("Invalid webhook secret on /webhook/trello")
        return {"status": "forbidden"}

    payload = await request.json()
    logger.info(f"Received Trello webhook: {str(payload)[:300]}")
    sync_tasks_to_leads()
    return {"status": "ok"}
