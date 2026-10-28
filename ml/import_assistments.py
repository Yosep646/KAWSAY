"""Convertidor de ASSISTments 2009-10 Skill Builder a secuencias de KAWSAY.

Fuente: https://sites.google.com/site/assistmentsdata/home/2009-2010-assistment-data/skill-builder-data-2009-2010
Uso: python -m ml.import_assistments --input /ruta/skill_builder_data.csv --output ml/datasets/raw/assistments.jsonl

Importante: el dataset no contiene grados escolares peruanos fiables. Por tanto
NO se asigna un grado ficticio para entrenar el modelo existente.
La salida conserva la habilidad, y requiere un pipeline específico de knowledge tracing.
"""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def convert(source: Path, target: Path, salt: str) -> dict:
    if len(salt) < 16:
        raise ValueError("Proporcione una sal privada de 16+ caracteres")
    sequences = defaultdict(list)
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        needed = {"user_id", "problem_id", "correct", "skill_id", "order_id"}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError(f"Faltan columnas: {sorted(needed - set(reader.fieldnames or []))}")
        seen = set()
        for row in reader:
            if row.get("original") not in (None, "", "1", "1.0"):
                continue
            if not row["user_id"] or not row["skill_id"] or row["correct"] not in ("0", "1", "0.0", "1.0"):
                continue
            key = (row["user_id"], row["problem_id"], row["order_id"])
            if key in seen:
                continue
            seen.add(key)
            sid = hashlib.sha256((salt + ":" + row["user_id"]).encode()).hexdigest()[:24]
            try:
                order = int(float(row["order_id"]))
                hints = min(20, max(0, int(float(row.get("hint_count") or 0))))
                attempts = max(1, int(float(row.get("attempt_count") or 1)))
            except (ValueError, OverflowError):
                continue
            sequences[sid].append({"order": order, "skill": row["skill_id"],
                                   "correct": int(float(row["correct"])),
                                   "hints": hints, "wrong": min(20, attempts - 1)})
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", encoding="utf-8") as out:
        for student, events in sorted(sequences.items()):
            events.sort(key=lambda e: e["order"])
            # Remove original log IDs: order is used only for ordering.
            results = [{k: v for k, v in event.items() if k != "order"} for event in events]
            out.write(json.dumps({"student": student, "results": results}) + "\n")
            count += len(results)
    return {"students": len(sequences), "interactions": count, "dataset": str(target),
            "status": "REAL_SOURCE_NOT_YET_VALIDATED", "requires_curriculum_mapping": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--salt", required=True, help="Secreto local; nunca incluir en Git")
    args = parser.parse_args()
    print(json.dumps(convert(args.input, args.output, args.salt), indent=2))
