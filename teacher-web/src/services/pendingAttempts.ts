/** Cola persistente por evento. Cada respuesta tiene ID único e idempotente para sincronización. */
export interface PendingAttempt {
  key: string; // usuario:actividad; los eventos se distinguen por event_id
  deviceId: string;
  event: { event_id: string; type: string; payload: Record<string, unknown> };
}
type Stored = PendingAttempt & { storageId: string };
function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("kawsay-student-pending", 2);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (db.objectStoreNames.contains("attempts")) {
        // Preserve records from v1 before upgrading their key structure.
        const old = req.transaction!.objectStore("attempts");
        const cursor = old.openCursor();
        const records: PendingAttempt[] = [];
        cursor.onsuccess = () => {
          if (cursor.result) { records.push(cursor.result.value as PendingAttempt); cursor.result.continue(); }
          else {
            db.deleteObjectStore("attempts");
            const store = db.createObjectStore("attempts", { keyPath: "storageId" });
            records.forEach(r => store.put({ ...r, storageId: r.event.event_id }));
          }
        };
      } else db.createObjectStore("attempts", { keyPath: "storageId" });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(new Error("No se pudo abrir el almacenamiento local."));
    req.onblocked = () => reject(new Error("Cierra las otras pestañas para actualizar el almacenamiento local."));
  });
}
async function withStore<T>(mode: IDBTransactionMode, fn: (store: IDBObjectStore, resolve: (value:T)=>void, reject:(error:Error)=>void)=>void): Promise<T> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("attempts", mode);
    let value:T; let done = false;
    fn(tx.objectStore("attempts"), v => {value=v;done=true;}, reject);
    tx.oncomplete = () => {db.close(); if(done) resolve(value); else reject(new Error("Operación local incompleta."));};
    tx.onerror = tx.onabort = () => {db.close(); reject(new Error("No se pudo acceder a las respuestas locales."));};
  });
}
export const pendingAttempts = {
  list: (key: string) => withStore<PendingAttempt[]>("readonly", (store, resolve, reject) => {
    const req = store.getAll();
    req.onsuccess = () => resolve((req.result as Stored[]).filter(r => r.key === key));
    req.onerror = () => reject(new Error("No se pudieron consultar las respuestas pendientes."));
  }),
  add: (record: PendingAttempt) => withStore<void>("readwrite", (store, resolve, reject) => {
    const req = store.add({...record, storageId:record.event.event_id});
    req.onsuccess = () => resolve();
    req.onerror = () => reject(new Error("No se pudo guardar la respuesta."));
  }),
  removeConfirmed: (key: string, eventId: string) => withStore<boolean>("readwrite", (store, resolve) => {
    const req = store.get(eventId);
    req.onsuccess = () => {
      const saved = req.result as Stored | undefined;
      if(saved?.key === key && saved.event.event_id === eventId) {store.delete(eventId); resolve(true);}
      else resolve(false);
    };
  }),
};
