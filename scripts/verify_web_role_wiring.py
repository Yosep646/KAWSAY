"""Static smoke check of front-end role routes/API wiring (not browser E2E)."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
app=(root/'teacher-web/src/app/App.tsx').read_text(encoding='utf-8')
api=(root/'teacher-web/src/services/api.ts').read_text(encoding='utf-8')
checks={
'admin protected': '<Protected roles={["ADMIN"]}><Admin' in app,
'docente protected': '<Protected roles={["TEACHER"]}><Dashboard' in app,
'estudiante protected': '<Protected roles={["STUDENT"]}><StudentHome' in app,
'activity route protected': '<Protected roles={["STUDENT"]}><StudentActivity' in app,
'shared API base': 'const API = `${BASE}/api/v1`' in api,
'auth login API': '"/auth/login"' in api,
'student login API': '"/auth/student-login"' in api,
'auth refresh API': '/auth/refresh' in api,
}
for name,passed in checks.items(): print(('PASS' if passed else 'FAIL')+' '+name)
raise SystemExit(0 if all(checks.values()) else 1)
