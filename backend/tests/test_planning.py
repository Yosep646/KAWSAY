import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.planning.models import CurriculumPlanVersion

FW = {"country_code": "PE", "name": "Marco DEMO", "version_label": "demo-1", "is_demo": True,
      "source_note": "Datos de muestra; NO es currículo oficial",
      "subjects": [{"name": "Matemática (DEMO)", "competencies": [
          {"name": "Resuelve problemas de cantidad (DEMO)", "capacities": ["Traduce cantidades (DEMO)"]},
          {"name": "Resuelve problemas de datos (DEMO)", "capacities": []}]},
          {"name": "Comunicación (DEMO)", "competencies": [{"name": "Lee textos (DEMO)", "capacities": []}]}]}


def _env(w):
    s1, s2 = w.school("E1"), w.school("E2")
    w.staff("ADMIN", "admin@x.pe")
    w.staff("TEACHER", "ta@x.pe", s1)
    w.staff("TEACHER", "tb@x.pe", s2)
    admin, ta, tb = w.login("admin@x.pe"), w.login("ta@x.pe"), w.login("tb@x.pe")
    fw = w.c.post("/api/v1/curriculum/frameworks", headers=admin, json=FW)
    assert fw.status_code == 201, fw.text
    tree = w.c.get(f"/api/v1/curriculum/frameworks/{fw.json()['id']}", headers=ta).json()
    return admin, ta, tb, fw.json()["id"], tree


def _build_draft(w, ta, fw_id, tree, year=2026):
    plan = w.c.post("/api/v1/planning/plans", headers=ta, json={"academic_year": year, "framework_id": fw_id,
                                                                "name": "Plan anual"})
    assert plan.status_code == 201, plan.text
    vid = plan.json()["version"]["id"]
    period = w.c.post(f"/api/v1/planning/versions/{vid}/periods", headers=ta, json={"name": "I Bimestre", "sequence": 1}).json()
    math = next(s for s in tree["subjects"] if s["name"].startswith("Matem"))
    comp = math["competencies"][0]
    unit = w.c.post(f"/api/v1/planning/versions/{vid}/units", headers=ta, json={
        "period_id": period["id"], "grade_id": w.grade_id(ta, 4), "subject_id": math["id"], "title": "Fracciones"})
    assert unit.status_code == 201, unit.text
    topic = w.c.post(f"/api/v1/planning/versions/{vid}/topics", headers=ta, json={
        "unit_id": unit.json()["id"], "competency_id": comp["id"], "capacity_id": comp["capacities"][0]["id"],
        "title": "Comparación de fracciones", "learning_objective": "Comparar fracciones con igual denominador"})
    assert topic.status_code == 201, topic.text
    return plan.json()["id"], vid, math, comp, unit.json()["id"]


def test_catalog_import_admin_only_and_demo_flag_explicit(w):
    admin, ta, _, _, tree = _env(w)
    assert tree["is_demo"] is True
    assert w.c.post("/api/v1/curriculum/frameworks", headers=ta, json=FW).status_code == 403
    no_flag = {k: v for k, v in FW.items() if k != "is_demo"} | {"name": "otro"}
    assert w.c.post("/api/v1/curriculum/frameworks", headers=admin, json=no_flag).status_code == 422
    assert w.c.post("/api/v1/curriculum/frameworks", headers=admin, json=FW).status_code == 409  # duplicado


def test_full_version_workflow_and_immutability(w):
    admin, ta, _, fw_id, tree = _env(w)
    _, vid, math, comp, unit_id = _build_draft(w, ta, fw_id, tree)
    api = "/api/v1/planning/versions"
    assert w.c.post(f"{api}/{vid}/approve", headers=admin).status_code == 409        # no está en revisión
    assert w.c.post(f"{api}/{vid}/submit", headers=ta).status_code == 200
    assert w.c.post(f"{api}/{vid}/approve", headers=ta).status_code == 403            # docente no aprueba
    assert w.c.post(f"{api}/{vid}/activate", headers=admin).status_code == 409        # falta approve
    assert w.c.post(f"{api}/{vid}/approve", headers=admin).status_code == 200
    assert w.c.post(f"{api}/{vid}/activate", headers=admin).status_code == 200
    # una versión no-DRAFT es inmutable
    r = w.c.post(f"{api}/{vid}/periods", headers=ta, json={"name": "II", "sequence": 2})
    assert r.status_code == 409


def test_new_version_archives_previous_without_changing_history(w):
    admin, ta, _, fw_id, tree = _env(w)
    plan_id, v1, *_ = _build_draft(w, ta, fw_id, tree)
    for step, who in (("submit", ta), ("approve", admin), ("activate", admin)):
        assert w.c.post(f"/api/v1/planning/versions/{v1}/{step}", headers=who).status_code == 200
    before = w.c.get(f"/api/v1/planning/versions/{v1}", headers=ta).json()
    v2 = w.c.post(f"/api/v1/planning/plans/{plan_id}/versions", headers=ta).json()
    assert v2["label"] == "2026.2" and v2["status"] == "DRAFT"
    v2_tree = w.c.get(f"/api/v1/planning/versions/{v2['id']}", headers=ta).json()
    assert [t["title"] for u in v2_tree["periods"][0]["units"] for t in u["topics"]] == ["Comparación de fracciones"]
    assert w.c.post(f"/api/v1/planning/plans/{plan_id}/versions", headers=ta).status_code == 409  # ya hay borrador
    for step, who in (("submit", ta), ("approve", admin), ("activate", admin)):
        assert w.c.post(f"/api/v1/planning/versions/{v2['id']}/{step}", headers=who).status_code == 200
    plans = w.c.get("/api/v1/planning/plans", headers=ta).json()
    assert {v["label"]: v["status"] for v in plans[0]["versions"]} == {"2026.1": "ARCHIVED", "2026.2": "ACTIVE"}
    assert w.c.get(f"/api/v1/planning/versions/{v1}", headers=ta).json()["periods"] == before["periods"]


def test_db_enforces_single_active_version(w, db):
    _, ta, _, fw_id, tree = _env(w)
    plan_id, v1, *_ = _build_draft(w, ta, fw_id, tree)
    from app.modules.users.models import User
    uid = db.query(User).filter_by(email="ta@x.pe").one().id
    db.query(CurriculumPlanVersion).update({"status": "ACTIVE", "approved_by": uid})
    db.add(CurriculumPlanVersion(plan_id=db.query(CurriculumPlanVersion).one().plan_id, label="2026.9",
                                 status="ACTIVE", created_by=uid, approved_by=uid))
    with pytest.raises(IntegrityError):
        db.commit()


def test_cross_school_isolation(w):
    admin, ta, tb, fw_id, tree = _env(w)
    plan_id, vid, *_ = _build_draft(w, ta, fw_id, tree)
    assert w.c.get(f"/api/v1/planning/versions/{vid}", headers=tb).status_code == 404
    assert w.c.post(f"/api/v1/planning/plans/{plan_id}/versions", headers=tb).status_code == 404
    assert w.c.post(f"/api/v1/planning/versions/{vid}/periods", headers=tb, json={"name": "x", "sequence": 3}).status_code == 404
    assert w.c.get("/api/v1/planning/plans", headers=tb).json() == []
    assert len(w.c.get("/api/v1/planning/plans", headers=admin).json()) == 1


def test_curricular_consistency_rules(w):
    admin, ta, _, fw_id, tree = _env(w)
    _, vid, math, comp, unit_id = _build_draft(w, ta, fw_id, tree)
    com = next(s for s in tree["subjects"] if s["name"].startswith("Comunic"))
    # competencia de otra área dentro de una unidad de Matemática
    bad = w.c.post(f"/api/v1/planning/versions/{vid}/topics", headers=ta, json={
        "unit_id": unit_id, "competency_id": com["competencies"][0]["id"], "title": "Tema fuera de área",
        "learning_objective": "Objetivo cualquiera válido"})
    assert bad.status_code == 409
    # capacidad que no pertenece a la competencia
    bad2 = w.c.post(f"/api/v1/planning/versions/{vid}/topics", headers=ta, json={
        "unit_id": unit_id, "competency_id": math["competencies"][1]["id"], "capacity_id": comp["capacities"][0]["id"],
        "title": "Capacidad ajena", "learning_objective": "Objetivo cualquiera válido"})
    assert bad2.status_code == 409
    # área de otro marco curricular
    fw2 = dict(FW, name="Otro marco")
    other = w.c.post("/api/v1/curriculum/frameworks", headers=admin, json=fw2).json()["id"]
    t2 = w.c.get(f"/api/v1/curriculum/frameworks/{other}", headers=ta).json()
    period = w.c.get(f"/api/v1/planning/versions/{vid}", headers=ta).json()["periods"][0]["id"]
    bad3 = w.c.post(f"/api/v1/planning/versions/{vid}/units", headers=ta, json={
        "period_id": period, "grade_id": w.grade_id(ta, 4), "subject_id": t2["subjects"][0]["id"], "title": "Área de otro marco"})
    assert bad3.status_code == 409
    # fechas inválidas / submit sin temas
    assert w.c.post(f"/api/v1/planning/versions/{vid}/periods", headers=ta, json={
        "name": "II", "sequence": 2, "start_date": "2026-05-01", "end_date": "2026-04-01"}).status_code == 422


def test_submit_requires_topics(w):
    _, ta, _, fw_id, _ = _env(w)
    vid = w.c.post("/api/v1/planning/plans", headers=ta, json={"academic_year": 2026, "framework_id": fw_id,
                                                               "name": "Vacío"}).json()["version"]["id"]
    assert w.c.post(f"/api/v1/planning/versions/{vid}/submit", headers=ta).status_code == 409


def test_active_plan_for_classroom_only_returns_active_version(w):
    admin, ta, tb, fw_id, tree = _env(w)
    room = w.classroom(ta)
    assert w.c.get(f"/api/v1/planning/active?classroom_id={room}", headers=ta).json() == []   # borrador no cuenta
    _, vid, *_ = _build_draft(w, ta, fw_id, tree)
    assert w.c.get(f"/api/v1/planning/active?classroom_id={room}", headers=ta).json() == []
    for step, who in (("submit", ta), ("approve", admin), ("activate", admin)):
        w.c.post(f"/api/v1/planning/versions/{vid}/{step}", headers=who)
    active = w.c.get(f"/api/v1/planning/active?classroom_id={room}", headers=ta).json()
    assert len(active) == 1 and active[0]["status"] == "ACTIVE" and active[0]["label"] == "2026.1"
    other_room = w.classroom(tb, "B")
    assert w.c.get(f"/api/v1/planning/active?classroom_id={room}", headers=tb).status_code == 404
    assert w.c.get(f"/api/v1/planning/active?classroom_id={other_room}", headers=tb).json() == []
