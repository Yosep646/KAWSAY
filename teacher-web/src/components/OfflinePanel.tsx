import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { Card, ErrorBox } from "./ui";
import { downloadStudentTasks, synchronizeOffline } from "../services/offlineLearning";
import { offlineVault, type VaultData } from "../services/offlineVault";
import { pendingAttempts } from "../services/pendingAttempts";
import { errMsg } from "../utils/format";

export function OfflinePanel() {
  const { user, onlineSession, loginStudent } = useAuth();
  const [data, setData] = useState<VaultData | null>(null);
  const [exists, setExists] = useState(false);
  const [phrase, setPhrase] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [code, setCode] = useState("");
  const [pin, setPin] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    if (typeof indexedDB === "undefined") return;
    void offlineVault.exists().then(async found => {
      if (!cancelled) setExists(found);
      if (offlineVault.isOpen(user?.id)) {
        const local = await offlineVault.snapshot();
        if (!cancelled) setData(local);
      }
    }).catch(e => { if (!cancelled) setError(errMsg(e)); });
    return () => { cancelled = true; };
  }, [user?.id]);

  async function prepare(e: FormEvent) {
    e.preventDefault();
    if (!user || busy || !onlineSession) return;
    setBusy(true); setError(null);
    try {
      if (exists) {
        setData(await offlineVault.unlock(phrase, user.id));
      } else {
        if (phrase !== confirmation) throw new Error("Las frases locales deben coincidir.");
        if (phrase.length < 12) throw new Error("Usa una frase local de al menos 12 caracteres.");
        if (import.meta.env.PROD) {
          if (!("serviceWorker" in navigator)) throw new Error("Este navegador no admite la descarga sin conexión.");
          const ready = await Promise.race([
            navigator.serviceWorker.ready,
            new Promise<never>((_resolve, reject) => setTimeout(() => reject(new Error("No se instaló la aplicación sin conexión. Mantén la conexión y vuelve a intentar.")), 15000)),
          ]);
          if (!ready.active) throw new Error("Espera a que termine la instalación sin conexión.");
        }
        if (await pendingAttempts.hasForStudent(user.id)) throw new Error("Confirma primero la respuesta pendiente de tu actividad en línea.");
        const deviceId = localStorage.getItem("kawsay_web_device_id");
        if (!deviceId) throw new Error("Vuelve a iniciar sesión para identificar este dispositivo.");
        const downloaded = await downloadStudentTasks(deviceId);
        await offlineVault.create({ user, deviceId, verifiedAt: Date.now(), ...downloaded, pending: [] }, phrase);
        setData(await offlineVault.snapshot()); setExists(true);
      }
      setPhrase(""); setConfirmation("");
      setMessage("Actividades protegidas. Guarda tu frase local: se necesita cada vez que cierres el navegador.");
    } catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  }

  async function sync() {
    if (!user || busy) return;
    setBusy(true); setError(null);
    try {
      const count = await synchronizeOffline(user.id);
      const downloaded = await downloadStudentTasks((await offlineVault.snapshot()).deviceId);
      setData(await offlineVault.update(local => { local.tasks = downloaded.tasks; local.statuses = downloaded.statuses; local.verifiedAt = Date.now(); }));
      setMessage(`${count} respuestas confirmadas. Actividades actualizadas.`);
    } catch (e) {
      setError(errMsg(e));
      if (offlineVault.isOpen(user.id)) setData(await offlineVault.snapshot());
    } finally { setBusy(false); }
  }

  return <Card title="Aprender sin conexión"><ErrorBox message={error} />{message && <p role="status">{message}</p>}
    {!data ? onlineSession ? <form className="stack" onSubmit={e => void prepare(e)}>
      <p>{exists ? "Desbloquea las actividades protegidas de esta cuenta." : "Descarga tus actividades y elige una frase local de al menos 12 caracteres. Este navegador guarda un estudiante a la vez."}</p>
      {!exists && <p>Elige una frase larga y distinta de tu PIN. Consérvala: si la olvidas no podrás recuperar las respuestas que aún no enviaste.</p>}
      <label>Frase para actividades descargadas<input type="password" minLength={12} maxLength={256} autoComplete="new-password" required value={phrase} onChange={e => setPhrase(e.target.value)} /></label>
      {!exists && <label>Repetir frase local<input type="password" required autoComplete="new-password" value={confirmation} onChange={e => setConfirmation(e.target.value)} /></label>}
      <button disabled={busy}>{busy ? "Preparando…" : exists ? "Abrir almacén protegido" : "Descargar y proteger actividades"}</button>
    </form> : <p>Abre tus actividades desde el acceso sin conexión.</p> : <>
      <p role="status">{data.pending.length} respuestas pendientes de confirmación. Los resultados oficiales se calculan al sincronizar.</p>
      <ul className="student-task-list">{data.tasks.map(task => <li key={task.student_assignment_id}><strong>{task.title}</strong><span>{task.subject ?? "Actividad educativa"}</span>
        <Link to={`/estudiante/descargada/${task.student_assignment_id}`}>Resolver actividad descargada</Link></li>)}</ul>
      {!data.tasks.length && <p>No hay actividades descargadas. Conéctate para actualizar.</p>}
      {onlineSession ? <><button disabled={busy} onClick={() => void sync()}>{busy ? "Sincronizando…" : "Sincronizar respuestas y actualizar"}</button>
        <button className="ghost" disabled={busy || data.pending.length > 0} onClick={() => {
          setBusy(true); setError(null);
          void offlineVault.removeDownloaded().then(() => { setData(null); setExists(false); setMessage("Actividades descargadas eliminadas de este navegador. Puedes volver a descargarlas con conexión."); })
            .catch(e => setError(errMsg(e))).finally(() => setBusy(false));
        }}>Quitar actividades descargadas</button></> : <form className="stack" onSubmit={e => {
        e.preventDefault(); setBusy(true); setError(null);
        void loginStudent(code, pin).then(() => setMessage("Sesión verificada. Ya puedes sincronizar.")).catch(e => setError(errMsg(e))).finally(() => { setBusy(false); setPin(""); });
      }}><p>Para sincronizar, recupera la conexión e inicia sesión con tu misma cuenta.</p>
        <label>Código para sincronizar<input required autoComplete="username" value={code} onChange={e => setCode(e.target.value)} /></label>
        <label>PIN para sincronizar<input required type="password" autoComplete="current-password" value={pin} onChange={e => setPin(e.target.value)} /></label>
        <button disabled={busy}>Verificar sesión para sincronizar</button>
      </form>}
    </>}
  </Card>;
}
