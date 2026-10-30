import type { UserBrief } from "../types/api";
import type { PendingAttempt } from "./pendingAttempts";

export interface LocalQuestion {
  id: string;
  type: "MULTIPLE_CHOICE" | "NUMERIC" | "SHORT_TEXT";
  prompt: string;
  options: string[] | null;
}
export interface LocalTask {
  student_assignment_id: string;
  title: string;
  subject: string | null;
  instructions: string;
  questions: LocalQuestion[];
}
export interface QuestionStatus { question_id: string; closed: boolean; device_attempt_number: number }
export interface VaultData {
  user: UserBrief;
  deviceId: string;
  verifiedAt: number;
  tasks: LocalTask[];
  statuses: Record<string, QuestionStatus[]>;
  pending: PendingAttempt[];
}
interface Envelope {
  id: "student";
  version: 1;
  owner: string;
  revision: number;
  iterations: number;
  salt: number[];
  iv: number[];
  ciphertext: number[];
}
const DB = "kawsay-encrypted-offline";
const ITERATIONS = 600_000;
const MAX_AGE = 7 * 24 * 60 * 60 * 1000;
const encoder = new TextEncoder();
let session: { owner: string; salt: number[]; key: CryptoKey } | null = null;

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB, 1);
    request.onupgradeneeded = () => request.result.createObjectStore("vault", { keyPath: "id" });
    request.onsuccess = () => resolve(request.result);
    request.onerror = request.onblocked = () => reject(new Error("No se pudo abrir el almacén protegido."));
  });
}

async function read(): Promise<Envelope | undefined> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("vault", "readonly");
    const request = tx.objectStore("vault").get("student");
    tx.oncomplete = () => { db.close(); resolve(request.result as Envelope | undefined); };
    tx.onabort = tx.onerror = () => { db.close(); reject(new Error("No se pudo leer el almacén protegido.")); };
  });
}

async function write(next: Envelope, expectedRevision?: number): Promise<void> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("vault", "readwrite");
    const store = tx.objectStore("vault");
    const request = store.get("student");
    request.onsuccess = () => {
      const current = request.result as Envelope | undefined;
      if (current?.revision !== expectedRevision || (current && current.owner !== next.owner)) { tx.abort(); return; }
      store.put(next);
    };
    tx.oncomplete = () => { db.close(); resolve(); };
    tx.onabort = tx.onerror = () => { db.close(); reject(new Error("No se guardaron los cambios. Recarga e inténtalo otra vez.")); };
  });
}

async function exclusive<T>(action: () => Promise<T>): Promise<T> {
  if (!navigator.locks || !crypto.subtle) throw new Error("Este navegador no admite el almacenamiento protegido. Usa Chrome actualizado con HTTPS o localhost.");
  return navigator.locks.request("kawsay-encrypted-offline", action);
}

function validEnvelope(record: Envelope): void {
  const bytes = (value: unknown, length?: number): value is number[] => Array.isArray(value)
    && (length === undefined || value.length === length) && value.every(n => Number.isInteger(n) && n >= 0 && n <= 255);
  if (record.version !== 1 || record.iterations !== ITERATIONS || !record.owner || !Number.isSafeInteger(record.revision)
      || !bytes(record.salt, 16) || !bytes(record.iv, 12) || !bytes(record.ciphertext) || record.ciphertext.length < 16) {
    throw new Error("El almacén protegido está dañado o utiliza una versión incompatible.");
  }
}

async function derive(phrase: string, salt: number[]): Promise<CryptoKey> {
  const material = await crypto.subtle.importKey("raw", encoder.encode(phrase), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({ name: "PBKDF2", hash: "SHA-256", salt: Uint8Array.from(salt), iterations: ITERATIONS },
    material, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}

function aad(owner: string, revision: number): Uint8Array {
  return encoder.encode(JSON.stringify(["kawsay-offline-v1", owner, revision]));
}

async function seal(data: VaultData, key: CryptoKey, salt: number[], revision: number): Promise<Envelope> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv, additionalData: aad(data.user.id, revision) },
    key, encoder.encode(JSON.stringify(data)));
  return { id: "student", version: 1, owner: data.user.id, revision, iterations: ITERATIONS, salt,
    iv: Array.from(iv), ciphertext: Array.from(new Uint8Array(ciphertext)) };
}

async function unseal(record: Envelope, key: CryptoKey): Promise<VaultData> {
  validEnvelope(record);
  const plaintext = await crypto.subtle.decrypt({ name: "AES-GCM", iv: Uint8Array.from(record.iv),
    additionalData: aad(record.owner, record.revision) }, key, Uint8Array.from(record.ciphertext));
  const data = JSON.parse(new TextDecoder().decode(plaintext)) as VaultData;
  if (data.user?.role !== "STUDENT" || data.user.id !== record.owner || !data.deviceId
      || !Number.isFinite(data.verifiedAt) || !Array.isArray(data.pending) || !Array.isArray(data.tasks)) {
    throw new Error("Contenido local inválido.");
  }
  return data;
}

async function current(): Promise<{ data: VaultData; record: Envelope; key: CryptoKey }> {
  const active = session;
  if (!active) throw new Error("Desbloquea primero tus actividades descargadas.");
  const record = await read();
  if (!record || record.owner !== active.owner) throw new Error("El almacén protegido cambió. Vuelve a abrirlo.");
  return { data: await unseal(record, active.key), record, key: active.key };
}

export const offlineVault = {
  async exists(): Promise<boolean> { return Boolean(await read()); },
  isOpen(studentId?: string): boolean { return Boolean(session && (!studentId || session.owner === studentId)); },
  lock(): void { session = null; },
  async create(data: VaultData, phrase: string): Promise<void> {
    if (phrase.length < 12 || phrase.length > 256 || !phrase.trim()) throw new Error("Usa una frase local de 12 a 256 caracteres.");
    if (data.user.role !== "STUDENT") throw new Error("Solo estudiantes pueden descargar actividades en este equipo.");
    await exclusive(async () => {
      if (await read()) throw new Error("Ya hay actividades protegidas en este navegador. Desbloquéalas con su frase local.");
      const salt = Array.from(crypto.getRandomValues(new Uint8Array(16)));
      const key = await derive(phrase, salt);
      await write(await seal(data, key, salt, 1));
      session = { owner: data.user.id, key, salt };
    });
  },
  async unlock(phrase: string, authenticatedStudentId?: string): Promise<VaultData> {
    session = null;
    return exclusive(async () => {
      const record = await read();
      if (!record) throw new Error("Primero descarga tus actividades con conexión.");
      validEnvelope(record);
      if (authenticatedStudentId && authenticatedStudentId !== record.owner) throw new Error("Las actividades descargadas pertenecen a otra cuenta.");
      const key = await derive(phrase, record.salt);
      let data: VaultData;
      try { data = await unseal(record, key); }
      catch { throw new Error("La frase local no es correcta o los datos están dañados."); }
      if (!authenticatedStudentId && (Date.now() < data.verifiedAt || Date.now() - data.verifiedAt > MAX_AGE)) {
        throw new Error("Conéctate e inicia sesión para renovar el acceso local de siete días. Tus respuestas siguen guardadas.");
      }
      if (authenticatedStudentId) {
        data.verifiedAt = Date.now();
        await write(await seal(data, key, record.salt, record.revision + 1), record.revision);
      }
      session = { owner: record.owner, key, salt: record.salt };
      return data;
    });
  },
  async snapshot(): Promise<VaultData> { return (await current()).data; },
  async removeDownloaded(): Promise<void> {
    await exclusive(async () => {
      const { data } = await current();
      if (data.pending.length) throw new Error("Sincroniza las respuestas pendientes antes de quitar las actividades.");
      const db = await open();
      await new Promise<void>((resolve, reject) => {
        const tx = db.transaction("vault", "readwrite");
        tx.objectStore("vault").delete("student");
        tx.oncomplete = () => { db.close(); resolve(); };
        tx.onabort = tx.onerror = () => { db.close(); reject(new Error("No se pudieron quitar las actividades descargadas.")); };
      });
      session = null;
    });
  },
  async update(change: (data: VaultData) => void): Promise<VaultData> {
    return exclusive(async () => {
      const { data, record, key } = await current();
      change(data);
      await write(await seal(data, key, record.salt, record.revision + 1), record.revision);
      return data;
    });
  },
  async enqueue(taskId: string, questionId: string, answer: Record<string, unknown>): Promise<VaultData> {
    return this.update(data => {
      if (Date.now() < data.verifiedAt || Date.now() - data.verifiedAt > MAX_AGE) {
        throw new Error("Conéctate e inicia sesión para renovar el acceso local. Tus respuestas siguen guardadas.");
      }
      const task = data.tasks.find(t => t.student_assignment_id === taskId);
      if (!task?.questions.some(q => q.id === questionId)) throw new Error("La pregunta no está descargada para esta cuenta.");
      if (data.pending.some(p => p.event.payload.student_assignment_id === taskId && p.event.payload.question_id === questionId)) {
        throw new Error("Esta pregunta ya tiene una respuesta pendiente.");
      }
      const status = data.statuses[taskId]?.find(s => s.question_id === questionId);
      if (status?.closed) throw new Error("Esta pregunta ya está completada.");
      const number = (status?.device_attempt_number ?? 0) + 1;
      if (number > 50) throw new Error("Consulta con tu docente antes de continuar esta pregunta.");
      data.pending.push({ key: `${data.user.id}:${taskId}`, deviceId: data.deviceId, event: {
        event_id: crypto.randomUUID(), type: "attempt.created", payload: { student_assignment_id: taskId,
          question_id: questionId, attempt_number: number, answer, hints_used: 0, response_time_ms: 0,
          client_created_at: new Date().toISOString() } } });
    });
  },
};
