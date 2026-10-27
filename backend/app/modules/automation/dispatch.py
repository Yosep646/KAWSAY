"""Entrega de eventos a n8n (u otro receptor) con firma HMAC. n8n es automatización SECUNDARIA:
si falla, los eventos quedan PENDING con backoff y el núcleo sigue funcionando."""
import hashlib
import hmac
import json
import math
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.automation.models import DomainEvent

MAX_ATTEMPTS = 8
BASE_BACKOFF = 30
MAX_BACKOFF = 3600


def sign(secret: str, timestamp: str, body: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), f"{timestamp}.{body}".encode(), hashlib.sha256).hexdigest()


def verify(secret: str, timestamp: str, body: str, signature: str, tolerance: int = 300) -> bool:
    """Para el receptor (p. ej. n8n): firma válida y timestamp reciente (anti-replay)."""
    try:
        ts = float(timestamp)
    except (TypeError, ValueError, OverflowError):
        return False
    if not math.isfinite(ts) or abs(time.time() - ts) > tolerance:
        return False
    return hmac.compare_digest(sign(secret, timestamp, body), signature)


def dispatch_pending(db: Session, client: httpx.Client | None = None, limit: int = 50) -> dict:
    s = get_settings()
    if not s.automation_webhook_url or not s.automation_webhook_secret:
        return {"status": "disabled", "delivered": 0, "failed": 0, "retry_later": 0}
    own = client is None
    client = client or httpx.Client(timeout=3.0)
    out: dict[str, Any] = {"status": "ok", "delivered": 0, "failed": 0, "retry_later": 0}
    now = datetime.now(UTC)
    try:
        due = [(e.id, e.type, e.payload, e.created_at.isoformat()) for e in db.scalars(
            select(DomainEvent).where(DomainEvent.status == "PENDING", DomainEvent.next_attempt_at <= now)
            .order_by(DomainEvent.created_at).limit(limit))]
        db.commit()  # SQLite: NO retener la transacción durante las llamadas HTTP (n8n puede tardar o caer)
        for ev_id, ev_type, payload, created in due:
            body = json.dumps({"event_id": str(ev_id), "type": ev_type, "created_at": created, "payload": payload},
                              separators=(",", ":"), sort_keys=True)
            ts = str(int(time.time()))
            try:
                r = client.post(s.automation_webhook_url, content=body, headers={
                    "content-type": "application/json", "X-Kawsay-Event-Id": str(ev_id),
                    "X-Kawsay-Timestamp": ts, "X-Kawsay-Signature": sign(s.automation_webhook_secret, ts, body)})
                err = None if 200 <= r.status_code < 300 else f"http_{r.status_code}"
            except httpx.HTTPError as exc:
                err = type(exc).__name__
            ev = db.get(DomainEvent, ev_id)
            if ev is None:
                continue
            ev.attempts += 1
            if err is None:
                ev.status, ev.delivered_at, ev.last_error = "DELIVERED", datetime.now(UTC), None
                out["delivered"] += 1
            elif ev.attempts >= MAX_ATTEMPTS:
                ev.status, ev.last_error = "FAILED", err
                out["failed"] += 1
            else:
                ev.last_error = err
                ev.next_attempt_at = datetime.now(UTC) + timedelta(seconds=min(BASE_BACKOFF * 2 ** ev.attempts, MAX_BACKOFF))
                out["retry_later"] += 1
            db.commit()
    finally:
        if own:
            client.close()
    return out
