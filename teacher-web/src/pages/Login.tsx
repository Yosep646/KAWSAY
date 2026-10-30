import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { ErrorBox } from "../components/ui";
import { errMsg } from "../utils/format";
import { Brand, BrandMark, Icon } from "../components/Icon";
import loginScene from "../assets/kawsay-fondo-responsive-20261028.webp";

type Role = "ADMIN" | "TEACHER" | "STUDENT";
const rememberedEmailKey = "kawsay_last_email";
function rememberedEmail() {
  try { return localStorage.getItem(rememberedEmailKey) ?? ""; } catch { return ""; }
}

export function Login() {
  const { login, loginStudent, unlockOffline } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState(rememberedEmail);
  const [remember, setRemember] = useState(() => Boolean(rememberedEmail()));
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState<Role>("ADMIN");
  const [staffRole, setStaffRole] = useState<"ADMIN" | "TEACHER">("ADMIN");
  const [helpOpen, setHelpOpen] = useState(false);
  const [code, setCode] = useState("");
  const [phrase, setPhrase] = useState("");
  const student = role === "STUDENT";

  const selectRole = (next: Role) => {
    if (next !== "STUDENT") setStaffRole(next);
    setRole(next); setErr(null); setPassword(""); setShowPassword(false); setHelpOpen(false);
  };
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      if (student) {
        await loginStudent(code, password); nav("/estudiante");
      } else {
        await login(email, password);
        // Remember only the email; credentials and session tokens are never saved here.
        try { if (remember) localStorage.setItem(rememberedEmailKey, email); else localStorage.removeItem(rememberedEmailKey); } catch { /* Optional preference. */ }
        nav("/");
      }
    } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  };
  return (
    <main id="kawsay-login" className="login-layout">
      <img className="login-scene-art" src={loginScene} alt="" aria-hidden="true" />
      <section className="login-story" aria-label="Bienvenida a KAWSAY AI">
        <Brand />
        <div className="login-story-copy">
          <span className="eyebrow">APRENDER · CRECER · ACOMPAÑAR</span>
          <h1><span>Más educación</span><span>para más</span><span className="login-highlight">comunidades.</span></h1>
          <p>Herramientas digitales para docentes, estudiantes e instituciones educativas del Perú.</p>
          <div className="login-values"><span><Icon name="book" />Aprender</span><span><Icon name="leaf" />Crecer</span><span><Icon name="students" />Acompañar</span></div>
        </div>
        <div className="login-story-footer"><Icon name="book" /><span>Educación adaptativa.<br /><strong>Decisiones siempre humanas.</strong></span></div>
      </section>
      <section className="login-form-panel" aria-labelledby="login-title">
        <div className="login">
          <header className="login-card-head">
            <span className="login-symbol"><BrandMark /></span>
            <h2 id="login-title">Bienvenido</h2>
            <p>Ingresa a tu cuenta</p>
          </header>
          <div className="login-role-tabs" role="group" aria-label="Tipo de usuario">
            {([["ADMIN", "Administrador"], ["TEACHER", "Docente"], ["STUDENT", "Estudiante"]] as const).map(([value, label]) => <button key={value} type="button" aria-pressed={role === value} disabled={busy} onClick={() => selectRole(value)}>{label}</button>)}
          </div>
          <div className="login-method-tabs" role="group" aria-label="Método de acceso">
            <button type="button" aria-pressed={!student} disabled={busy} onClick={() => selectRole(staffRole)}>Correo y contraseña</button>
            <button type="button" aria-pressed={student} disabled={busy} onClick={() => selectRole("STUDENT")}>Código y PIN</button>
          </div>
          <form onSubmit={e => void submit(e)} className="login-access-form">
            <div className="login-field"><label htmlFor="login-identity">{student ? "Código de estudiante" : "Correo"}</label>
              <span className="login-input-wrap"><Icon name="mail" /><input id="login-identity" type={student ? "text" : "email"} value={student ? code : email} onChange={e => student ? setCode(e.target.value) : setEmail(e.target.value)} autoComplete="username" autoCapitalize="none" spellCheck={false} required /></span>
            </div>
            <div className="login-field"><label htmlFor="password">{student ? "PIN" : "Contraseña"}</label>
              <span className="login-input-wrap password-field"><Icon name="lock" /><input id="password" type={showPassword ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" inputMode={student ? "numeric" : undefined} required /><button type="button" className="password-toggle" aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"} aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}><Icon name={showPassword ? "eyeOff" : "eye"} /></button></span>
            </div>
            <div className="login-preferences">
              {student ? <span>Usa el código y PIN de tu institución.</span> : <label className="login-remember" title="Recuerda únicamente tu correo en este dispositivo"><input type="checkbox" checked={remember} onChange={e => { setRemember(e.target.checked); if (!e.target.checked) { try { localStorage.removeItem(rememberedEmailKey); } catch { /* Optional preference. */ } } }} />Recordarme</label>}
              <button className="login-forgot" type="button" aria-expanded={helpOpen} aria-controls="login-recovery" onClick={() => setHelpOpen(!helpOpen)}>{student ? "¿Olvidaste tu PIN?" : "¿Olvidaste tu contraseña?"}</button>
            </div>
            {helpOpen && <p id="login-recovery" className="login-recovery">{student ? "Solicita a tu docente o a la administración de tu institución que restablezcan tu PIN." : "Contacta a la administración de tu institución para recuperar el acceso a tu cuenta."}</p>}
            <ErrorBox message={err} />
            <button type="submit" className="login-submit" disabled={busy}>{busy ? "Ingresando…" : "Ingresar"}<Icon name="arrow" /></button>
          </form>
          <details className="login-offline"><summary>Abrir actividades descargadas sin conexión</summary>
            <form className="stack" onSubmit={e => { e.preventDefault(); setBusy(true); setErr(null);
              void unlockOffline(phrase).then(() => nav("/estudiante")).catch(x => setErr(errMsg(x))).finally(() => { setBusy(false); setPhrase(""); }); }}>
              <p>Usa la frase local que elegiste al descargar. Para enviar tus respuestas necesitarás volver a iniciar sesión con conexión.</p>
              <label>Frase local<input type="password" value={phrase} onChange={e => setPhrase(e.target.value)} autoComplete="off" required /></label>
              <button disabled={busy}>Desbloquear actividades</button>
            </form>
          </details>
          <p className="login-help">¿Necesitas acceso? Contacta a la administración de tu institución.</p>
          <div className="login-footnote"><Icon name="students" />Educación que acompaña a cada comunidad</div>
        </div>
      </section>
    </main>
  );
}
