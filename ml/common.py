"""Reutiliza EXACTAMENTE las reglas de puntuación de producción (backend/app/domain/adaptive.py)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))

from app.domain import adaptive  # noqa: E402

MODELS_DIR = ROOT / "models"
REGISTRY_PATH = ROOT / "registry" / "registry.json"
REPORTS_DIR = ROOT / "reports"
HISTORY = 10          # ejercicios cerrados usados como entrada
HORIZON = 5           # ejercicios futuros que se predicen
TARGET_MIN_DIFFICULT = 3   # etiqueta = >=3 de los próximos 5 con dificultad
FEATURES = ["mean_score_10", "mean_score_5", "min_score_10", "std_score_10", "frac_difficult_10",
            "frac_difficult_5", "hints_per_ex_10", "wrong_per_ex_10", "trend_10", "last3_mean", "grade"]
# Variables que NUNCA se usan como entrada (sensibles / identificadores):
FORBIDDEN_FEATURES = {"student", "name", "dni", "language", "mother_language", "community", "region", "gps"}


def read_json(path: Path):
    """UTF-8 para artefactos nuevos; admite informes históricos de Windows."""
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    return json.loads(text)
