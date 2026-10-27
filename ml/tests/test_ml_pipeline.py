import json

import numpy as np
import pytest

from ml import export_real, predict, registry, synthetic, train
from ml.common import FEATURES, FORBIDDEN_FEATURES
from ml.features import build_windows, dataset_version, group_split, validate_sequences


def test_synthetic_generation_is_deterministic_and_features_clean():
    a, b = synthetic.simulate_sequences(50, seed=1), synthetic.simulate_sequences(50, seed=1)
    assert a == b and a != synthetic.simulate_sequences(50, seed=2)
    Xa, ya, *_ = build_windows(a)
    Xb, yb, *_ = build_windows(b)
    assert dataset_version(Xa, ya, {"s": 1}) == dataset_version(Xb, yb, {"s": 1})
    assert Xa.shape[1] == len(FEATURES) and not (set(FEATURES) & FORBIDDEN_FEATURES)


def test_group_split_has_no_student_leakage():
    X, y, groups, _ = build_windows(synthetic.simulate_sequences(120, seed=3))
    masks, parts = group_split(groups, seed=3)
    assert not (parts["train"] & parts["val"]) and not (parts["train"] & parts["test"]) and not (parts["val"] & parts["test"])
    assert sum(int(m.sum()) for m in masks.values()) == len(y)
    for name, m in masks.items():
        assert set(groups[m].tolist()) == parts[name]


def test_inner_calibration_also_separates_students():
    X, y, groups, _ = build_windows(synthetic.simulate_sequences(90, seed=3))
    for tr, va in train.grouped_folds(X, y, groups, 3):
        assert not set(groups[tr]) & set(groups[va])
        for inner_tr, inner_va in train.grouped_folds(X[tr], y[tr], groups[tr], 3):
            assert not set(groups[tr][inner_tr]) & set(groups[tr][inner_va])


@pytest.mark.parametrize("field,value", [("score", float("nan")), ("score", 1.1), ("hints", -1), ("wrong", True)])
def test_dataset_rejects_invalid_measurements(field, value):
    seq = synthetic.simulate_sequences(1, seed=1)
    seq[0]["results"][0][field] = value
    with pytest.raises(ValueError):
        validate_sequences(seq)


def test_dataset_rejects_personal_columns_and_empty_data():
    seq = synthetic.simulate_sequences(1, seed=1)
    seq[0]["display_name"] = "dato que no debe exportarse"
    with pytest.raises(ValueError):
        validate_sequences(seq)
    with pytest.raises(ValueError):
        validate_sequences([])


def test_label_uses_only_future_and_features_only_past():
    seq = [{"student": "S", "grade": 3, "results": [{"score": 1.0, "hints": 0, "wrong": 0}] * 10
            + [{"score": 0.0, "hints": 1, "wrong": 3}] * 5}]
    X, y, *_ = build_windows(seq)
    assert len(y) == 1 and y[0] == 1                      # pasado perfecto, futuro difícil
    assert X[0][FEATURES.index("mean_score_10")] == 1.0    # el futuro no se filtra a las features


def test_training_smoke_and_registry_blocks_synthetic_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "REGISTRY_PATH", tmp_path / "reg.json")
    monkeypatch.setattr(train, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(train, "REPORTS_DIR", tmp_path / "reports")
    r = train.run("synthetic", students=300, seed=5, quick=True)
    assert r["data_kind"] == "SYNTHETIC" and 0.5 < r["test"]["roc_auc"] <= 1.0 and "SINTÉTICOS" in r["limitations"][0]
    mid = r["model_id"]
    assert registry.list_models()[0]["status"] == "CANDIDATE"
    with pytest.raises(registry.RegistryError):
        registry.approve(mid, "Revisor Humano")            # sintético: nunca aprobado
    with pytest.raises(registry.RegistryError):
        registry.approve(mid, "")
    # inferencia: sin modelo APPROVED se niega salvo modo experimental explícito
    monkeypatch.setattr(predict, "MODELS_DIR", tmp_path / "models")
    hist = [{"score": 0.4, "hints": 1, "wrong": 1}] * 10
    with pytest.raises(predict.NoApprovedModel):
        predict.predict(hist, 3)
    out = predict.predict(hist, 3, allow_experimental=True)
    assert out["model_status"] == "CANDIDATE" and "EXPERIMENTAL" in out["warning"] and 0 <= out["probability"] <= 1
    assert predict.predict(hist[:4], 3)["status"] == "INSUFFICIENT_EVIDENCE"


def test_real_data_guard_refuses_small_datasets():
    with pytest.raises(export_real.InsufficientDataError):
        export_real.check_sufficiency(n_students=3, n_long_sequences=0)
    export_real.check_sufficiency(n_students=500, n_long_sequences=400)   # suficiente: no lanza


def test_training_real_file_cannot_bypass_minimum_dataset_size(tmp_path):
    data = tmp_path / "real.jsonl"
    data.write_text("\n".join(json.dumps(s) for s in synthetic.simulate_sequences(3, seed=1)), encoding="utf-8")
    with pytest.raises(export_real.InsufficientDataError):
        train.run(source="real", data=data, write=False, quick=True)


def test_inference_rejects_synthetic_model_marked_approved(monkeypatch):
    monkeypatch.setattr(registry, "list_models", lambda: [
        {"model_id": "synthetic", "status": "APPROVED", "data_kind": "SYNTHETIC"},
    ])
    with pytest.raises(predict.NoApprovedModel):
        predict.load()


def test_pseudonymization_is_stable_salted_and_hides_id():
    a = export_real.pseudonymize("uuid-1", "sal-secreta-0123456789")
    assert a == export_real.pseudonymize("uuid-1", "sal-secreta-0123456789")
    assert a != export_real.pseudonymize("uuid-1", "otra-sal-0123456789ab") and "uuid-1" not in a
    json.dumps({"student": a})


def test_no_numpy_nans_in_features():
    X, *_ = build_windows(synthetic.simulate_sequences(40, seed=9))
    assert np.isfinite(X).all()


def test_cv_report_has_grouped_folds_confidence_intervals_and_calibration(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "REGISTRY_PATH", tmp_path / "reg.json")
    r = train.run("synthetic", students=250, seed=3, write=False, quick=True)
    assert r["cv"]["grouped_by"] == "student" and r["cv"]["folds"] == 3 and r["chosen"] in r["cv"]["results"]
    for k in ("roc_auc", "pr_auc", "f1"):
        lo, hi = r["test_ci95"][k]
        assert lo <= hi and 0 <= lo and hi <= 1
    assert 0 <= r["test"]["ece"] <= 0.5 and r["calibration"].startswith("sigmoid")
    assert set(r["error_by_grade_band"]) == {"grados_1-2", "grados_3-4", "grados_5-6"}


def test_export_real_sql_path_on_sqlite_is_pseudonymized_and_guarded(tmp_path):
    import sqlite3
    from datetime import datetime, timedelta, timezone
    db = tmp_path / "k.db"
    con = sqlite3.connect(db)
    con.executescript("""
      CREATE TABLE grades(id INTEGER PRIMARY KEY, number INTEGER, level TEXT);
      CREATE TABLE student_profiles(user_id TEXT PRIMARY KEY, grade_id INTEGER, display_name TEXT);
      CREATE TABLE learning_attempts(id TEXT, student_user_id TEXT, competency_id TEXT, question_id TEXT, attempt_number INTEGER,
        is_correct INTEGER, hints_used INTEGER, effective_at TEXT);
      INSERT INTO grades VALUES (1, 3, 'PRIMARIA'), (2, 3, 'SECUNDARIA');
      INSERT INTO student_profiles VALUES ('stu-1', 1, 'Nombre Real Del Niño');
      INSERT INTO student_profiles VALUES ('stu-2', 2, 'Estudiante de secundaria');""")
    t0 = datetime(2026, 5, 4, tzinfo=timezone.utc)
    for i in range(16):
        con.execute("INSERT INTO learning_attempts VALUES (?,?,?,?,?,?,?,?)",
                    (f"a{i}", "stu-1", "comp-1", f"q{i}", 1, 1, 0, (t0 + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S.%f")))
        con.execute("INSERT INTO learning_attempts VALUES (?,?,?,?,?,?,?,?)",
                    (f"b{i}", "stu-2", "comp-1", f"q{i}", 1, 1, 0, (t0 + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S.%f")))
    con.commit()
    con.close()
    out = tmp_path / "real.jsonl"
    with pytest.raises(export_real.InsufficientDataError):
        export_real.export(f"sqlite:///{db}", "sal-secreta-0123456789", out)          # 1 estudiante: se niega
    assert not out.exists()
    with pytest.raises(ValueError):
        export_real.export(f"sqlite:///{db}", "short", out, min_students=1, min_sequences=1)
    assert not out.exists()
    res = export_real.export(f"sqlite:///{db}", "sal-secreta-0123456789", out, min_students=1, min_sequences=1)
    text = out.read_text()
    assert res["students"] == 1 and res["long_sequences"] == 1
    assert len(text.splitlines()) == 1
    assert "Nombre Real" not in text and "stu-1" not in text and '"student": "P' in text   # sin nombre ni id real
