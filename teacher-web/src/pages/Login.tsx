import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { ErrorBox } from "../components/ui";
import { errMsg } from "../utils/format";
import { Brand, Icon } from "../components/Icon";

export function Login() {
  const { login, loginStudent } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [student, setStudent] = useState(false);
  const [code, setCode] = useState("");

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try { if (student) { await loginStudent(code, password); nav("/estudiante"); } else { await login(email, password); nav("/"); } } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  };
  return (
    <main className="login-layout">
      <section className="login-story" aria-label="Bienvenida a KAWSAY AI">
        <Brand />
        <div className="login-story-copy"><span className="eyebrow">APRENDER · CRECER · ACOMPAÑAR</span><h1>Que nadie se quede<br />atrás.</h1><p>Cada aula es un mundo. Cada estudiante, una oportunidad de aprender a su manera.</p><div className="story-principle"><Icon name="book" /><span>Educación adaptativa.<br /><strong>Decisiones siempre humanas.</strong></span></div></div>
        <svg className="landscape" viewBox="0 0 600 300" fill="none" aria-hidden="true"><circle cx="450" cy="65" r="35" fill="#e9c779" /><path d="m0 240 160-180 140 160L410 90l190 150v60H0Z" fill="#367a69" /><path d="m112 114 48-54 43 55-43-16Z" fill="#abc4a2" /><path d="m0 260 170-90 180 100 140-110 110 85v55H0Z" fill="#205c50" /><path d="M0 285c140-80 220 60 350-5s160-45 250-5v25H0Z" fill="#154b42" /><path d="m280 300 48-36-18-12 30-15" stroke="#d2b980" strokeWidth="12" /></svg>
        <p className="login-story-footer">Diseñado para la diversidad de nuestras aulas.</p>
      </section>
      <section className="login-form-panel">
      <div className="login">
      <span className="login-symbol"><Icon name="leaf" /></span>
      <p className="eyebrow">{student ? "Espacio estudiante" : "Docencia y administración"}</p>
      <h2>Bienvenido a tu aula</h2>
      <p className="muted login-description">Ingresa para planificar, descubrir avances y acompañar a tus estudiantes.</p>
      <button type="button" className="ghost" onClick={() => { setStudent(!student); setErr(null); setPassword(""); }}>{student ? "Acceso docente o administrador" : "Soy estudiante"}</button>
      <form onSubmit={(e) => void submit(e)} className="stack">
        {student ? <label>Código de estudiante<input value={code} onChange={(e) => setCode(e.target.value)} autoComplete="username" required /></label> : <label>Correo<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required /></label>}
        <label htmlFor="password">{student ? "PIN" : "Contraseña"}</label>
        <div className="password-field"><input id="password" type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /><button type="button" className="password-toggle" aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"} aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}><Icon name="eye" /></button></div>
        <ErrorBox message={err} />
        <button type="submit" className="login-submit" disabled={busy}>{busy ? "Ingresando…" : "Ingresar"}<Icon name="arrow" /></button>
      </form>
      <p className="login-help">¿Necesitas acceso? Contacta a la administración de tu institución.</p>
      <div className="login-footnote"><Icon name="students" /> Un espacio para docentes y administración</div>
      </div>
      </section>
    </main>
  );
}
