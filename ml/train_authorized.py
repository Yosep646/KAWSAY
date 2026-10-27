"""Entrenamiento EXCLUSIVAMENTE con dataset real autorizado y validado.
Uso: python -m ml.train_authorized --data /ruta/real.jsonl --quick
No crea datos sintéticos y no aprueba automáticamente el modelo.
"""
import argparse
from pathlib import Path
from ml import export_real
from ml.features import validate_sequences
from ml.train import load_sequences, run
from ml.common import HISTORY, HORIZON


def main() -> None:
    cli = argparse.ArgumentParser(description="Entrenar KAWSAY AI usando solamente datos reales autorizados")
    cli.add_argument("--data", type=Path, required=True, help="JSONL de historiales autorizados")
    cli.add_argument("--seed", type=int, default=7)
    cli.add_argument("--quick", action="store_true")
    args = cli.parse_args()
    if not args.data.is_file():
        cli.error("No existe un dataset real autorizado. No se reemplazará por datos sintéticos.")
    seqs, kind = load_sequences("real", 0, args.seed, args.data)
    assert kind == "REAL"
    validate_sequences(seqs)
    export_real.check_sufficiency(len({s["student"] for s in seqs}), sum(len(s["results"]) >= HISTORY + HORIZON for s in seqs))
    print(f"Datos reales verificados: {len(seqs)} historiales. Iniciando entrenamiento reproducible.")
    report = run(source="real", seed=args.seed, data=args.data, quick=args.quick)
    print(report)
    print("Modelo CANDIDATE: su publicación requiere validación y aprobación independientes.")

if __name__ == "__main__":
    main()
