"""Prueba REAL de IndexedDB y Service Worker en Chromium (requiere `pip install playwright` + `tsc`).

Solo ejercita las primitivas offline y el shell PWA, no la autenticación offline.
"""
from __future__ import annotations

import functools
import http.server
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="kawsay-offline-") as d:
        root = Path(d)
        subprocess.run([
            "tsc", "--target", "ES2022", "--module", "ES2022", "--lib", "ES2022,DOM",
            "--strict", "--skipLibCheck", "--outDir", str(root),
            str(ROOT / "teacher-web/src/services/pendingAttempts.ts"),
            str(ROOT / "teacher-web/src/services/offlineTasks.ts"),
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        shutil.copy(ROOT / "teacher-web/public/sw.js", root / "sw.js")
        (root / "index.html").write_text("<!DOCTYPE html><meta charset='utf-8'><title>KAWSAY offline smoke</title><main>KAWSAY OFFLINE TEST</main>")
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with sync_playwright() as pw:
                path = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
                options = {"executable_path": path} if path else {}
                browser = pw.chromium.launch(**options)
                context = browser.new_context(service_workers="allow")
                page = context.new_page()
                page.goto(base)
                actual = page.evaluate("""async () => {
                   const {pendingAttempts: q} = await import('/pendingAttempts.js');
                   const {offlineTasks: tasks} = await import('/offlineTasks.js');
                   const mk = (id, key) => ({ key, deviceId: 'device-1', event: {event_id:id,type:'attempt.created',payload:{question_id:id}} });
                   await q.add(mk('e1','studentA:activity1'));
                   await q.add(mk('e2','studentA:activity1'));
                   await q.add(mk('e3','studentB:activity1'));
                   const before = await q.list('studentA:activity1');
                   const denied = await q.removeConfirmed('studentB:activity1','e1');
                   const removed = await q.removeConfirmed('studentA:activity1','e1');
                   const after = await q.list('studentA:activity1');
                   const others = await q.list('studentB:activity1');
                   await tasks.save('studentA',[{student_assignment_id:'activity1',title:'Matemática',questions:[{id:'q1',type:'SHORT_TEXT',prompt:'Hola',options:null}]}]);
                   await tasks.save('studentA',[{student_assignment_id:'activity1',title:'Matemática renovada'}]);
                   await tasks.save('studentB',[{student_assignment_id:'activity1',title:'Otra actividad'}]);
                   const local = await tasks.list('studentA');
                   await tasks.clear('studentA');
                   const cleared = await tasks.list('studentA');
                   const isolated = await tasks.list('studentB');
                   return { before:before.length, denied, removed, after:after.length, others:others.length, kept:local[0]?.questions?.length, cleared:cleared.length, isolated:isolated.length };
                 }""")
                assert actual == {"before":2,"denied":False,"removed":True,"after":1,"others":1,"kept":1,"cleared":0,"isolated":1}, actual
                print("PASS IndexedDB: múltiples eventos, ACK, separación por alumno, conservación de preguntas")
                page.evaluate("navigator.serviceWorker.register('/sw.js')")
                page.evaluate("navigator.serviceWorker.ready")
                page.reload()
                page.wait_for_function("navigator.serviceWorker.controller !== null")
                context.set_offline(True)
                page.goto(base + '/estudiante', wait_until='domcontentloaded')
                assert 'KAWSAY OFFLINE TEST' in page.locator('body').inner_text()
                print("PASS Service Worker: navegación offline con shell previamente descargado")
                context.set_offline(False)
                browser.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    run()
