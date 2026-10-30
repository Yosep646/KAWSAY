/** Cola durable mínima; no contiene tokens y se limita a una respuesta por actividad y usuario. */
export interface PendingAttempt {
  key: string;
  deviceId: string;
  event: { event_id: string; type: string; payload: Record<string, unknown> };
}

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("kawsay-student-pending", 1);
    req.onupgradeneeded = () => req.result.createObjectStore("attempts", { keyPath: "key" });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(new Error("No se pudo abrir el almacenamiento local."));
    req.onblocked = () => reject(new Error("El almacenamiento local está bloqueado por otra pestaña."));
  });
}

async function transaction<T>(mode: IDBTransactionMode, action: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("attempts", mode);
    const req = action(tx.objectStore("attempts"));
    tx.oncomplete = () => { db.close(); resolve(req.result); };
    tx.onabort = tx.onerror = () => { db.close(); reject(new Error("No se pudo guardar o recuperar la respuesta local.")); };
  });
}

export const pendingAttempts = {
  async hasForStudent(studentId: string): Promise<boolean> {
    return (await transaction<PendingAttempt[]>("readonly", store => store.getAll())).some(r => r.key.startsWith(`${studentId}:`));
  },
  get: (key: string) => transaction<PendingAttempt | undefined>("readonly", store => store.get(key)),
  add: (record: PendingAttempt) => transaction<IDBValidKey>("readwrite", store => store.add(record)),
  async removeConfirmed(key: string, eventId: string): Promise<boolean> {
    const db = await open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction("attempts", "readwrite");
      const store = tx.objectStore("attempts");
      const req = store.get(key);
      let removed = false;
      req.onsuccess = () => {
        const record = req.result as PendingAttempt | undefined;
        if (record?.event.event_id === eventId) { store.delete(key); removed = true; }
      };
      tx.oncomplete = () => { db.close(); resolve(removed); };
      tx.onabort = tx.onerror = () => { db.close(); reject(new Error("No se pudo confirmar la respuesta local.")); };
    });
  },
};
