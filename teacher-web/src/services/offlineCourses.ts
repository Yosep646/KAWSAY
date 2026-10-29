/** Catálogo curricular local por estudiante. No almacena contraseñas ni tokens. */
export interface OfflineCourse {
  id: string;
  subject_id: string;
  name: string;
  classroom_id: string;
  classroom_name: string;
  academic_year: number;
  grade_id: number;
  is_demo: boolean;
}

function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("El navegador no admite almacenamiento de cursos sin conexión."));
      return;
    }
    const req = indexedDB.open("kawsay-offline-courses", 1);
    req.onupgradeneeded = () => req.result.createObjectStore("catalog", { keyPath: "studentId" });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(new Error("No se pudo abrir el catálogo de cursos local."));
  });
}

export const offlineCourses = {
  async save(studentId: string, courses: OfflineCourse[]): Promise<void> {
    const db = await database();
    try {
      await new Promise<void>((resolve, reject) => {
        const tx = db.transaction("catalog", "readwrite");
        tx.objectStore("catalog").put({ studentId, courses });
        tx.oncomplete = () => resolve();
        tx.onerror = tx.onabort = () => reject(new Error("No se pudo guardar el catálogo offline."));
      });
    } finally { db.close(); }
  },
  async list(studentId: string): Promise<OfflineCourse[]> {
    const db = await database();
    try {
      return await new Promise<OfflineCourse[]>((resolve, reject) => {
        const tx = db.transaction("catalog", "readonly");
        const req = tx.objectStore("catalog").get(studentId);
        req.onsuccess = () => resolve((req.result as { courses: OfflineCourse[] } | undefined)?.courses ?? []);
        req.onerror = () => reject(new Error("No se pudo leer el catálogo offline."));
      });
    } finally { db.close(); }
  },
};
