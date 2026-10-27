"""Worker: python -m app.workers.dispatcher  (entrega eventos pendientes cada 15 s; tolera caídas de n8n)."""
import logging
import time

from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.core.logging import configure_logging
from app.modules.automation.dispatch import dispatch_pending

log = logging.getLogger("kawsay.worker")


def main() -> None:
    configure_logging("INFO")
    while True:
        try:
            with Session(get_engine()) as db:
                res = dispatch_pending(db)
            if res.get("delivered") or res.get("failed"):
                log.info("dispatch", extra={"extra_fields": res})
        except Exception:
            log.exception("dispatch_error")
        time.sleep(15)


if __name__ == "__main__":
    main()
