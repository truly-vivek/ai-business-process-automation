import json
import re
import httpx
from pypdf import PdfReader
from io import BytesIO
from .config import settings

def extract_document_text(filename: str, content: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "pdf":
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if suffix in {"txt", "md", "csv"}:
        return content.decode("utf-8", errors="replace").strip()
    raise ValueError("Supported document types are PDF, TXT, MD and CSV")

def classify_enquiry(text: str) -> dict:
    """Deterministic baseline classifier; works without an external AI key."""
    lowered = text.lower()
    categories = {
        "billing": ("invoice", "payment", "refund", "billing", "charge"),
        "technical": ("error", "bug", "not working", "broken", "technical"),
        "sales": ("pricing", "quote", "demo", "purchase", "subscription"),
        "support": ("help", "support", "question", "assistance"),
    }
    category = next((name for name, words in categories.items() if any(w in lowered for w in words)), "general")
    priority = "high" if any(w in lowered for w in ("urgent", "asap", "critical", "outage")) else "normal"
    email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
    return {
        "category": category,
        "priority": priority,
        "email": email_match.group(0) if email_match else "",
        "summary": " ".join(text.split())[:500],
        "method": "rules",
    }

async def notify_webhook(payload: dict) -> dict:
    url = settings.notification_webhook_url
    if not url:
        return {"sent": False, "reason": "NOTIFICATION_WEBHOOK_URL is not configured"}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
    return {"sent": True, "status_code": response.status_code}
