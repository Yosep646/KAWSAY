"""Inventario reproducible sin leer secretos, bases de datos ni dependencias.

Comprueba sintaxis Python/JSON e igualdad binaria; no sustituye una revisión
semántica ni certifica funcionalidades por la mera existencia de archivos.
"""
import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", "env", "node_modules", "__pycache__",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build",
        ".dart_tool", "test-results", "playwright-report"}
TEXT = {".py", ".dart", ".ts", ".tsx", ".css", ".html", ".json", ".yaml",
        ".yml", ".toml", ".ini", ".txt", ".md", ".sh", ".cjs", ".conf", ".mako", ".example"}


def inventory() -> dict:
    files, excluded = [], defaultdict(int)
    hashes = defaultdict(list)

    def walk(folder):
        for p in sorted(folder.iterdir()):
            if p.is_symlink():
                excluded["enlace simbólico"] += 1
            elif p.is_dir():
                if p.name in SKIP or p.name.startswith(".kawsay-e2e-"):
                    excluded[p.name] += 1
                else:
                    yield from walk(p)
            elif p.name == ".env" or (p.name.startswith(".env.") and p.name != ".env.example"):
                excluded["configuración secreta (contenido no leído)"] += 1
            else:
                yield p

    for p in walk(ROOT):
        rel = p.relative_to(ROOT).as_posix()
        if rel in {"docs/INVENTARIO_ARCHIVOS.json", "docs/INVENTARIO_ARCHIVOS.md"}:
            continue
        entry = {"path": rel, "bytes": p.stat().st_size, "check": "inventariado; revisión funcional no demostrada"}
        if p.suffix in TEXT or p.name in {"Dockerfile", ".gitignore", ".dockerignore"}:
            content = p.read_bytes()
            entry["sha256"] = digest = hashlib.sha256(content).hexdigest()
            if content.strip():
                hashes[digest].append(rel)
            try:
                try:
                    text = content.decode("utf-8-sig")
                except UnicodeDecodeError:
                    text = content.decode("cp1252")
                    entry["encoding_note"] = "Codificación heredada cp1252; normalizar al editar"
                entry["lines"] = len(text.splitlines())
                if p.suffix == ".py":
                    ast.parse(text, filename=rel)
                    entry["check"] = "sintaxis Python válida; no certifica ejecución"
                elif p.suffix == ".json":
                    json.loads(text)
                    entry["check"] = "JSON válido; no certifica contrato"
            except (SyntaxError, ValueError) as exc:
                entry["check"] = f"error estructural: {type(exc).__name__}"
        else:
            entry["check"] = "binario/datos preservados; contenido no inspeccionado"
        files.append(entry)
    return {"scope": "Inventario y análisis estructural, no auditoría semántica completa",
            "files": files, "excluded_directories_or_secrets": dict(excluded),
            "identical_nonempty_text_files": [v for v in hashes.values() if len(v) > 1]}


def main():
    report = inventory()
    docs = ROOT / "docs"
    (docs / "INVENTARIO_ARCHIVOS.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Inventario estructural por archivo", "", report["scope"], "",
             "Los secretos se excluyen sin leerlos. Las coincidencias de hash no autorizan eliminaciones.", "",
             "| Ruta | Tamaño (bytes) | Evidencia |", "|---|---:|---|"]
    lines.extend(f"| `{f['path']}` | {f['bytes']} | {f['check']} |" for f in report["files"])
    (docs / "INVENTARIO_ARCHIVOS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Inventariados {len(report['files'])} archivos. Informe: docs/INVENTARIO_ARCHIVOS.md")


if __name__ == "__main__":
    main()
