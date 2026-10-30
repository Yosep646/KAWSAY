"""Demo de extremo a extremo contra un servidor KAWSAY en ejecución. TODOS los datos son DEMO.

Uso:  KAWSAY_URL=http://127.0.0.1:8000 KAWSAY_ADMIN_EMAIL=... KAWSAY_ADMIN_PASSWORD=... python scripts/demo_e2e.py
Simula el cliente móvil (que aún no existe) hablando el MISMO contrato HTTP que usará la app Flutter.
"""
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta

import httpx

BASE = os.environ.get("KAWSAY_URL", "http://127.0.0.1:8000").rstrip("/")
ADMIN = (os.environ["KAWSAY_ADMIN_EMAIL"], os.environ["KAWSAY_ADMIN_PASSWORD"])
TEACHER_EMAIL = os.environ.get("KAWSAY_TEACHER_EMAIL", "maestra@demo.pe")
TEACHER_PW = os.environ.get("KAWSAY_TEACHER_PASSWORD", "Aula-Multigrado-2026!")
c = httpx.Client(base_url=BASE + "/api/v1", timeout=20)


def step(msg):
    print(f"\n== {msg}")


def ok(r, code=200):
    if r.status_code != code:
        sys.exit(f"FALLO {r.request.method} {r.request.url} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.content else None


def auth(token):
    return {"Authorization": f"Bearer {token}"}


run = uuid.uuid4().hex[:6]
step("1. Admin crea escuela, docente y marco curricular DEMO")
adm = auth(ok(c.post("/auth/login", json={"email": ADMIN[0], "password": ADMIN[1]}))["access_token"])
school = ok(c.post("/schools", headers=adm, json={"name": f"Escuela DEMO {run}"}), 201)
t_email = TEACHER_EMAIL
r = c.post("/users", headers=adm, json={"role": "TEACHER", "email": t_email, "password": TEACHER_PW,
                                        "display_name": "Maestra DEMO", "school_id": school["id"]})
if r.status_code not in (201, 409):   # 409 = ya existe de una ejecución anterior: se reutiliza
    sys.exit(f"FALLO creando docente: {r.status_code} {r.text[:200]}")
fw = ok(c.post("/curriculum/frameworks", headers=adm, json={
    "country_code": "PE", "name": f"Marco DEMO {run}", "version_label": "demo", "is_demo": True,
    "source_note": "Datos de demostración; NO es currículo oficial",
    "subjects": [{"name": "Matemática (DEMO)", "competencies": [
        {"name": "Resuelve problemas de cantidad (DEMO)", "capacities": ["Traduce cantidades (DEMO)"]}]}]}), 201)
tree = ok(c.get(f"/curriculum/frameworks/{fw['id']}", headers=adm))
subject, comp = tree["subjects"][0], tree["subjects"][0]["competencies"][0]
print(f"   escuela={school['name']}  marco is_demo={tree['is_demo']}")

step("2. Docente: planificación por institución (versión 2026.1 → revisión → aprobación admin → ACTIVA)")
tch = auth(ok(c.post("/auth/login", json={"email": t_email, "password": TEACHER_PW}))["access_token"])
grades = {(g["level"], g["number"]): g["id"] for g in ok(c.get("/curriculum/grades", headers=tch))}
plan = ok(c.post("/planning/plans", headers=tch, json={"academic_year": 2026, "framework_id": fw["id"],
                                                       "name": "Plan anual DEMO"}), 201)
vid = plan["version"]["id"]
period = ok(c.post(f"/planning/versions/{vid}/periods", headers=tch, json={"name": "I Bimestre", "sequence": 1}), 201)
topics = {}
for g, title in ((1, "Comparar cantidades hasta 20"), (2, "Comparar cantidades hasta 100"), (3, "Comparar fracciones simples")):
    u = ok(c.post(f"/planning/versions/{vid}/units", headers=tch, json={
        "period_id": period["id"], "grade_id": grades[("PRIMARIA", g)], "subject_id": subject["id"],
        "title": f"Unidad {g}.º (DEMO)"}), 201)
    topics[g] = ok(c.post(f"/planning/versions/{vid}/topics", headers=tch, json={
        "unit_id": u["id"], "competency_id": comp["id"], "title": f"{title} (DEMO)",
        "learning_objective": f"Objetivo DEMO {g}.º: {title.lower()}"}), 201)["id"]
ok(c.post(f"/planning/versions/{vid}/submit", headers=tch))
ok(c.post(f"/planning/versions/{vid}/approve", headers=adm))
print("   estado final:", ok(c.post(f"/planning/versions/{vid}/activate", headers=adm))["status"])

step("3. Aula multigrado 1.º + 2.º + 3.º con estudiantes (código + PIN)")
room = ok(c.post("/classrooms", headers=tch, json={"name": f"Aula multigrado {run}", "academic_year": 2026}), 201)
kids = {n: ok(c.post("/students", headers=tch, json={"display_name": n, "grade_id": grades[("PRIMARIA", g)],
                                                      "classroom_id": room["id"]}), 201)
        for n, g in (("Juan", 1), ("Ana", 2), ("María", 3))}
print("   grados presentes:", ok(c.get(f"/classrooms/{room['id']}", headers=tch))["grades_present"])

step("4. Actividad base → 3 variantes (una por grado) → revisión docente → aprobación → publicación")
a = ok(c.post("/assignments", headers=tch, json={
    "classroom_id": room["id"], "title": "Comparamos cantidades", "instructions": "Elige la respuesta correcta",
    "grade_topics": [{"grade_id": grades[("PRIMARIA", g)], "topic_id": topics[g]} for g in (1, 2, 3)]}), 201)
for v in a["variants"]:
    g = next(k[1] for k, i in grades.items() if i == v["grade_id"])
    p = f"/assignments/{a['id']}/variants/{v['id']}"
    ok(c.patch(p, headers=tch, json={"title": f"Variante {g}.º (DEMO)",
                                     "instructions": f"Instrucciones adaptadas para {g}.º grado"}))
    qs = [{"type": "MULTIPLE_CHOICE", "prompt": f"[{g}.º] Ejercicio {i + 1}: ¿cuál es mayor?", "options": ["menor", "mayor"],
           "correct_answer": {"index": 1}, "hints": ["Compara con calma", "Usa material concreto"]} for i in range(5)]
    ok(c.put(p + "/questions", headers=tch, json={"questions": qs}))
    ok(c.post(p + "/review", headers=tch))
    ok(c.post(p + "/approve", headers=tch))
pub = ok(c.post(f"/assignments/{a['id']}/publish", headers=tch))
print(f"   publicada; estudiantes asignados={pub['students_assigned']}")

step("5. Cada estudiante inicia sesión y SINCRONIZA (pull) — recibe SOLO la variante de su grado")
tasks, sess = {}, {}
dev = {n: str(uuid.uuid4()) for n in kids}
for n, k in kids.items():
    tok = ok(c.post("/auth/student-login", json={"login_code": k["login_code"], "pin": k["pin"], "device_id": dev[n]}))
    sess[n] = auth(tok["access_token"])
    pulled = ok(c.get("/sync/pull", headers=sess[n]))
    tasks[n] = pulled["tasks"][0]
    print(f"   {n}: «{tasks[n]['title']}» | objetivo: {tasks[n]['learning_objective']}")

step("6. SIN INTERNET: el cliente trabaja local y encola eventos con UUID (simulado)")


def attempt(task, qi, n, correct, hints, minute):
    return {"event_id": str(uuid.uuid4()), "type": "attempt.created", "payload": {
        "student_assignment_id": task["student_assignment_id"], "question_id": task["questions"][qi]["id"],
        "attempt_number": n, "answer": {"index": 1 if correct else 0}, "is_correct": correct, "hints_used": hints,
        "response_time_ms": 6000, "client_created_at": (datetime.now(UTC) - timedelta(hours=3, minutes=-minute)).isoformat()}}


queues = {"Juan": [], "Ana": [], "María": []}
m = 0
for qi, steps in {0: [(0, 1), (0, 1), (0, 0)], 1: [(0, 1), (0, 1), (0, 0)], 2: [(0, 0), (0, 1), (1, 1)],
                  3: [(1, 0)], 4: [(0, 0), (0, 0), (0, 0)]}.items():   # Juan: 4 de 5 con dificultad, 6 pistas
    for n, (ok_, h) in enumerate(steps, start=1):
        queues["Juan"].append(attempt(tasks["Juan"], qi, n, bool(ok_), h, m))
        m += 1
for nm in ("Ana", "María"):                                              # el resto avanza sin dificultad
    for qi in range(5):
        queues[nm].append(attempt(tasks[nm], qi, 1, True, 0, qi))
print("   eventos pendientes:", {k: len(v) for k, v in queues.items()})

step("7. VUELVE INTERNET: push idempotente; luego se reenvía TODO (reintento accidental)")
for nm, ev in queues.items():
    first = ok(c.post("/sync/push", headers=sess[nm], json={"device_id": dev[nm], "events": ev}))["results"]
    again = ok(c.post("/sync/push", headers=sess[nm], json={"device_id": dev[nm], "events": ev}))["results"]
    print(f"   {nm}: 1.º envío {sorted({r['status'] for r in first})} | reenvío {sorted({r['status'] for r in again})}")

step("8. DASHBOARD DOCENTE (datos reales calculados en el servidor)")
summ = ok(c.get(f"/analytics/classrooms/{room['id']}/summary", headers=tch))
print("   resumen:", {k: summ[k] for k in ("students_total", "students_by_grade", "attempts_total", "open_support_flags")})
flags = ok(c.get(f"/support-flags?classroom_id={room['id']}", headers=tch))
print(f"   alertas abiertas: {len(flags)}")
for f in flags:
    print("   →", f["message"])
    print("     evidencia:", {k: f["evidence"][k] for k in ("difficult", "window", "hints_total", "wrong_attempts_total")},
          "| regla", f["rule_id"], "v" + f["rule_version"])
for n, k in kids.items():
    pr = ok(c.get(f"/analytics/classrooms/{room['id']}/students/{k['id']}/progress", headers=tch))["competencies"]
    print(f"   progreso {n}: {[(x['score'], x['state']) for x in pr]}")

step("9. Intervención docente registrada (la evolución se mostrará sin afirmar causalidad)")
f0 = flags[0]
iv = ok(c.post("/interventions", headers=tch, json={"student_id": f0["student"]["id"], "competency_id": f0["competency"]["id"],
                                                    "strategy": "Actividad guiada con material concreto", "support_flag_id": f0["id"]}), 201)
print("   intervención:", iv["id"], "| alerta ahora:", ok(c.get("/support-flags?status=ACKNOWLEDGED", headers=tch))[0]["status"])

step("10. Controles de seguridad en vivo")
print("   estudiante → API docente:", c.get("/classrooms", headers=sess["Juan"]).status_code, "(esperado 403)")
print("   sin token → analítica:", c.get(f"/analytics/classrooms/{room['id']}/summary").status_code, "(esperado 401)")
print("   docente ajeno/ID inventado → aula:", c.get(f"/classrooms/{uuid.uuid4()}", headers=tch).status_code, "(esperado 404)")
print("\nOK: flujo completo ejecutado contra", BASE)
