"""Despacho periódico de eventos educativos a n8n.

Solo se inicia en un servidor expresamente configurado. El envío de webhooks
no interrumpe el login, ni los ejercicios, ni la sincronización de respuestas.
"""
import asyncio
import logging

from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.modules.automation.dispatch import dispatch_pending

logger = logging.getLogger("kawsay.automation")


def dispatch_once() -> dict:
    """Una sesión de SQLite por ciclo, liberada antes del siguiente."""
    with Session(get_engine()) as db:
        return dispatch_pending(db)


async def dispatch_loop(interval_seconds: int = 15) -> None:
    """Autoentrega en segundo plano, cancelable al detener FastAPI."""
    while True:
        try:
            result = await asyncio.to_thread(dispatch_once)
            if result.get("delivered") or result.get("failed"):
                logger.info("webhook_dispatch %s", result)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("webhook_dispatch_failed")
        await asyncio.sleep(max(5, interval_seconds))
