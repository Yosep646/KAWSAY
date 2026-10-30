"""Single-origin web/API entry point for the isolated Render demonstration."""
import os
import mimetypes
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.main import create_app


def create_deployment_app(web_directory: str | Path):
    # Minimal container images may not have a system MIME database for WebP.
    mimetypes.add_type("image/webp", ".webp")
    app = create_app()
    directory = Path(web_directory).resolve()
    index = directory / "index.html"
    if not index.is_file():
        raise RuntimeError("The compiled frontend is missing")
    app.mount("/assets", StaticFiles(directory=directory / "assets"), name="web_assets")

    @app.get("/sw.js", include_in_schema=False)
    def service_worker():
        worker = directory / "sw.js"
        if not worker.is_file():
            raise HTTPException(status_code=404)
        return FileResponse(worker, media_type="application/javascript", headers={
            "Cache-Control": "no-cache", "Service-Worker-Allowed": "/", "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; connect-src 'self'"})

    @app.get("/{path:path}", include_in_schema=False)
    def web_shell(path: str):
        if path.split("/", 1)[0] in {"api", "health", "ready", "docs", "openapi.json", "favicon.ico"}:
            raise HTTPException(status_code=404)
        return FileResponse(index, media_type="text/html", headers={
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; worker-src 'self'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; "
                "connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
        })
    return app


def application():
    return create_deployment_app(os.environ["KAWSAY_SERVE_WEB_DIR"])
