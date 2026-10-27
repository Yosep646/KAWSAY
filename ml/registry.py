import json
from datetime import datetime, timezone

from ml.common import REGISTRY_PATH, read_json


class RegistryError(Exception):
    pass


def _load() -> list[dict]:
    return read_json(REGISTRY_PATH) if REGISTRY_PATH.exists() else []


def _save(items: list[dict]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")


def register(entry: dict) -> str:
    items = _load()
    entry = {**entry, "status": "CANDIDATE", "reviewed_by": None, "reviewed_at": None,
             "created_at": datetime.now(timezone.utc).isoformat()}
    items.append(entry)
    _save(items)
    return entry["model_id"]


def list_models() -> list[dict]:
    return _load()


def approve(model_id: str, reviewer: str, path=None) -> dict:
    """Revisión humana obligatoria. Un modelo entrenado con datos SINTÉTICOS nunca se aprueba."""
    items = _load()
    m = next((x for x in items if x["model_id"] == model_id), None)
    if m is None:
        raise RegistryError("modelo no encontrado")
    if not reviewer or not reviewer.strip():
        raise RegistryError("se requiere el nombre del revisor humano")
    if m["data_kind"] != "REAL":
        raise RegistryError("un modelo entrenado con datos no reales NO puede aprobarse para producción")
    m.update(status="APPROVED", reviewed_by=reviewer.strip(), reviewed_at=datetime.now(timezone.utc).isoformat())
    _save(items)
    return m
