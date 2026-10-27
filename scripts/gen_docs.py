"""Genera docs/07-er-diagram.md (desde los modelos SQLAlchemy) y docs/08-api.md (desde OpenAPI). Nada escrito a mano.
Uso: python scripts/gen_docs.py"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("JWT_SECRET", "docs_generation_secret_docs_generation_1234")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import models_registry  # noqa: E402,F401
from app.core.database import Base  # noqa: E402
from app.main import create_app  # noqa: E402


def er() -> str:
    lines = [
        "# 07 · Modelo entidad-relación (generado)", "",
        "_Generado por `python scripts/gen_docs.py` desde los modelos reales; no editar a mano._", "",
        f"Tablas: **{len(Base.metadata.tables)}**. `PK` clave primaria, `FK` clave foránea, `UK` única. "
        "Reglas de borrado: `RESTRICT` en todo el historial educativo (nunca se borra en cascada); "
        "`CASCADE` solo en `refresh_tokens`.", "", "```mermaid", "erDiagram",
    ]
    rel = []
    for t in sorted(Base.metadata.tables.values(), key=lambda x: x.name):
        lines.append(f"  {t.name} {{")
        fks = {c.name for fk in t.foreign_keys for c in [fk.parent]}
        for c in t.columns:
            tag = " PK" if c.primary_key else (" FK" if c.name in fks else (" UK" if c.unique else ""))
            typ = str(c.type).split("(")[0].replace(" ", "_") or "X"
            lines.append(f"    {typ} {c.name}{tag}")
        lines.append("  }")
        for fk in t.foreign_keys:
            nullable = fk.parent.nullable
            optional = " (opcional)" if nullable else ""
            rel.append(f"  {fk.column.table.name} ||--o{{ {t.name} : \"{fk.parent.name}{optional}\"")
    lines += sorted(set(rel)) + ["```", "", "## Restricciones relevantes (CHECK / índices parciales / triggers)"]
    for t in sorted(Base.metadata.tables.values(), key=lambda x: x.name):
        cks = [c for c in t.constraints if c.__class__.__name__ == "CheckConstraint" and c.name]
        idx = [i for i in t.indexes if i.unique and i.dialect_options["sqlite"]["where"] is not None]
        if cks or idx:
            descriptions = [f"`{c.name}`" for c in cks] + [f"índice único parcial `{i.name}`" for i in idx]
            lines.append(f"- **{t.name}**: " + "; ".join(descriptions))
    lines += [
        "- **learning_attempts**: triggers `trg_learning_attempts_no_update` / `_no_delete` "
        "(append-only, definidos en la migración)."
    ]
    return "\n".join(lines) + "\n"


def api() -> str:
    spec = create_app().openapi()
    by_tag: dict[str, list[str]] = {}
    for path, ops in sorted(spec["paths"].items()):
        for method, op in ops.items():
            tag = (op.get("tags") or ["otros"])[0]
            summary = op.get("summary", "").replace("|", "/")
            by_tag.setdefault(tag, []).append(f"| `{method.upper()}` | `{path}` | {summary} |")
    endpoint_count = sum(len(v) for v in by_tag.values())
    out = [
        "# 08 · API REST (generada)", "",
        "_Generada por `python scripts/gen_docs.py` desde OpenAPI. Documentación interactiva en `/docs` "
        "(solo fuera de producción)._", "",
        f"Versión **{spec['info']['version']}** · {endpoint_count} endpoints · prefijo `/api/v1` "
        "(sondas `/health`, `/ready` sin prefijo).", "",
        "## Convenciones", "- JSON; errores `{code, message, request_id, details?}`; sin trazas internas.",
        "- Autenticación `Authorization: Bearer <access token>` (15 min) + refresh token con rotación.",
        "- Roles: `STUDENT`, `TEACHER`, `ADMIN`. La autorización se valida en el servidor; los recursos ajenos "
        "responden **404** (no revelan existencia).",
        "- Límite de payload 1 MiB; se exige `Content-Length` en POST/PUT/PATCH; rate limit en login, "
        "refresh, IA y tutor.", "", "## Quién puede qué (resumen)", "| Rol | Puede |", "|---|---|",
        "| ADMIN | usuarios, escuelas, UGEL, marcos curriculares, aprobar/activar planificaciones, verificar "
        "traducciones, auditoría, automatización |",
        "| TEACHER | sus aulas y estudiantes, planificaciones de su escuela (borrador), actividades y variantes, "
        "adaptación con IA, publicación, alertas, intervenciones, analítica de sus aulas |",
        "| STUDENT | iniciar sesión (código+PIN), `sync`, mis tareas, quiero aprender, tutor, mi progreso, "
        "mis idiomas |", "",
    ]
    for tag, rows in sorted(by_tag.items()):
        out += [f"## {tag}", "| Método | Ruta | Descripción |", "|---|---|---|", *rows, ""]
    return "\n".join(out)


if __name__ == "__main__":
    (ROOT / "docs" / "07-er-diagram.md").write_text(er(), encoding="utf-8")
    (ROOT / "docs" / "08-api.md").write_text(api(), encoding="utf-8")
    (ROOT / "docs" / "openapi.json").write_text(json.dumps(create_app().openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
    print("docs/07-er-diagram.md, docs/08-api.md y docs/openapi.json generados")
