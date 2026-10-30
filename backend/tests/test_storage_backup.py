"""Respaldo SQLite de verdad, control de roles y conservación de registros."""
import sqlite3
from contextlib import closing


def _admin(w) -> dict:
    w.staff("ADMIN", "backup-admin@kawsay.com")
    return w.login("backup-admin@kawsay.com")


def test_admin_storage_status_reports_truth_without_guarantee(w):
    admin = _admin(w)
    status = w.c.get("/api/v1/admin/storage/status", headers=admin)
    assert status.status_code == 200, status.text
    body = status.json()
    assert body["database"] == "ok"
    assert body["engine"] == "SQLite"
    assert body["manual_backup_available"] is True
    assert body["storage_persistence"] == "not_verified"
    assert "almacenamiento" in body["message"].lower()


def test_admin_can_download_consistent_database_with_actual_records(w, tmp_path):
    school = w.school("Escuela para copia de seguridad")
    admin = _admin(w)
    response = w.c.get("/api/v1/admin/storage/export", headers=admin)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/octet-stream")
    assert 'attachment; filename="kawsay-respaldo-' in response.headers["content-disposition"]
    assert response.headers["cache-control"].startswith("no-store")  # el middleware fuerza no-store
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.content.startswith(b"SQLite format 3\x00")

    recovered = tmp_path / "recovered.db"
    recovered.write_bytes(response.content)
    with closing(sqlite3.connect(recovered)) as raw:
        assert raw.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert raw.execute("PRAGMA foreign_key_check").fetchone() is None
        row = raw.execute("SELECT name FROM schools WHERE id=?", (school.id.hex,)).fetchone()
        assert row == ("Escuela para copia de seguridad",)
        assert raw.execute("SELECT COUNT(*) FROM users WHERE role='ADMIN'").fetchone()[0] >= 1


def test_backup_is_protected_against_unauthorized_access(w):
    w.school()
    anonymous_status = w.c.get("/api/v1/admin/storage/status")
    anonymous_export = w.c.get("/api/v1/admin/storage/export")
    assert anonymous_status.status_code == 401
    assert anonymous_export.status_code == 401

    school = w.school("Escuela docente")
    w.staff("TEACHER", "backup-teacher@kawsay.com", school)
    teacher = w.login("backup-teacher@kawsay.com")
    assert w.c.get("/api/v1/admin/storage/status", headers=teacher).status_code == 403
    assert w.c.get("/api/v1/admin/storage/export", headers=teacher).status_code == 403
