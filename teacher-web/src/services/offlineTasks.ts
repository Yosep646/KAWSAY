/** Caché explícita, por estudiante, de actividades descargadas. Sin contraseñas ni tokens. */
export interface OfflineTask { student_assignment_id: string; title: string; subject?: string | null; instructions?: string; questions?: {id:string;type:string;prompt:string;options:string[]|null}[] }
function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("kawsay-offline-activities", 1);
    request.onupgradeneeded = () => { if (!request.result.objectStoreNames.contains("tasks")) request.result.createObjectStore("tasks", {keyPath:"key"}); };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(new Error("No se pudo abrir la biblioteca local."));
  });
}
export const offlineTasks = {
  async save(studentId: string, tasks: OfflineTask[]): Promise<void> {
    const db = await database();
    try { await new Promise<void>((resolve, reject) => {
      const tx = db.transaction("tasks", "readwrite"); const store = tx.objectStore("tasks");
      tasks.forEach(task => {
        const key = `${studentId}:${task.student_assignment_id}`;
        // A summary from /sync/pull must never erase already downloaded questions.
        const get = store.get(key);
        get.onsuccess = () => {
          const previous = (get.result as { task?: OfflineTask } | undefined)?.task;
          const keepQuestions = (!task.questions?.length && previous?.questions?.length)
            ? previous.questions : task.questions;
          store.put({ key, studentId, task: { ...previous, ...task, questions: keepQuestions } });
        };
      });
      tx.oncomplete = () => resolve(); tx.onerror = tx.onabort = () => reject(new Error("No se pudieron guardar las actividades."));
    }); } finally { db.close(); }
  },
  async list(studentId: string): Promise<OfflineTask[]> {
    const db = await database();
    try { return await new Promise((resolve, reject) => {
      const tx = db.transaction("tasks", "readonly"); const req = tx.objectStore("tasks").getAll();
      req.onsuccess = () => resolve((req.result as {studentId:string;task:OfflineTask}[]).filter(item => item.studentId === studentId).map(item => item.task));
      req.onerror = () => reject(new Error("No se pudieron leer las actividades guardadas."));
    }); } finally { db.close(); }
  },
  async clear(studentId: string): Promise<void> {
    const db = await database();
    try { await new Promise<void>((resolve, reject) => {
      const tx = db.transaction("tasks", "readwrite"); const req = tx.objectStore("tasks").openCursor();
      req.onsuccess = () => { const cursor = req.result; if (!cursor) return; if (String(cursor.key).startsWith(studentId+":")) cursor.delete(); cursor.continue(); };
      tx.oncomplete = () => resolve(); tx.onerror = tx.onabort = () => reject(new Error("No se pudo borrar la biblioteca local."));
    }); } finally { db.close(); }
  },
};
