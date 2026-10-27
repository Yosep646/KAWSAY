import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { ErrorBox } from "../components/ui";
import { errMsg } from "../utils/format";
import { Brand, Icon } from "../components/Icon";

type LoginRole = "ADMIN" | "TEACHER" | "STUDENT";
const REMEMBER_EMAIL_KEY = "kawsay_last_email";

function storedEmail(): string {
  try { return localStorage.getItem(REMEMBER_EMAIL_KEY) ?? ""; } catch { return ""; }
}

/** Acceso único: personal con correo/contraseña; estudiantes con correo o código/PIN. */
export function Login() {
  const { login, loginStudent, loginStudentEmail } = useAuth();
  const nav = useNavigate();
  const [role, setRole] = useState<LoginRole>("ADMIN");
  const [email, setEmail] = useState(storedEmail);
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [studentMethod, setStudentMethod] = useState<"email" | "code">("email");
  const [rememberEmail, setRememberEmail] = useState(() => !!storedEmail());
  const [helpOpen, setHelpOpen] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const student = role === "STUDENT";
  const codeMode = student && studentMethod === "code";

  const chooseRole = (next: LoginRole) => {
    if (busy) return;
    setRole(next);
    setErr(null);
    setPassword("");
    setShowPassword(false);
    setHelpOpen(false);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true); setErr(null);
    try {
      if (student) {
        if (studentMethod === "email") await loginStudentEmail(email.trim(), password);
        else await loginStudent(code.trim(), password);
        nav("/estudiante", { replace: true });
      } else {
        await login(email.trim(), password);
        nav("/", { replace: true });
      }
      // Recordar únicamente el correo, NUNCA la contraseña o un token de autenticación.
      try {
        if (rememberEmail && !codeMode) localStorage.setItem(REMEMBER_EMAIL_KEY, email.trim());
        else localStorage.removeItem(REMEMBER_EMAIL_KEY);
      } catch { /* Modo privado: no persistir preferencias. */ }
    } catch (reason) { setErr(errMsg(reason)); }
    finally { setBusy(false); }
  };

  return <main className="login-layout login-reimagined">
    <section className="login-story" aria-label="Bienvenida a KAWSAY AI">
      <Brand />
      <div className="login-story-copy">
        <span className="eyebrow">APRENDER · CRECER · ACOMPAÑAR</span>
        <h1>Más educación<br/>para más<br/><span className="login-highlight">comunidades.</span></h1>
        <p>Herramientas digitales para docentes, estudiantes e instituciones educativas del Perú.</p>
        <div className="login-values" aria-label="Nuestros valores">
          <span><Icon name="book"/> Aprender</span>
          <span><Icon name="leaf"/> Crecer</span>
          <span><Icon name="students"/> Acompañar</span>
        </div>
      </div>
      <p className="login-story-footer"><Icon name="book"/> <span>Educación adaptativa.<strong>Decisiones siempre humanas.</strong></span></p>
    </section>

    <section className="login-form-panel" aria-label="Acceso a la plataforma">
      <div className="login" role="region" aria-labelledby="login-title">
        <div className="login-card-head">
          <span className="login-symbol"><Icon name="leaf" /></span>
          <h2 id="login-title">Bienvenido</h2>
          <p className="muted login-description">Ingresa a tu cuenta</p>
        </div>

        <div className="login-role-tabs" role="group" aria-label="Tipo de usuario">
          {(["ADMIN", "TEACHER", "STUDENT"] as const).map((kind) =>
            <button type="button" key={kind} onClick={() => chooseRole(kind)}
              className={role === kind ? "active" : ""}
              aria-pressed={role === kind} disabled={busy}>
              {kind === "ADMIN" ? "Administrador" : kind === "TEACHER" ? "Docente" : "Estudiante"}
            </button>
          )}
        </div>

        {student && <div className="student-login-method" role="group" aria-label="Tipo de acceso del estudiante">
          <button type="button" className={studentMethod === "email" ? "active" : ""}
            aria-pressed={studentMethod === "email"} onClick={() => { setStudentMethod("email"); setErr(null); setPassword(""); }}>
            Correo y contraseña
          </button>
          <button type="button" className={studentMethod === "code" ? "active" : ""}
            aria-pressed={studentMethod === "code"} onClick={() => { setStudentMethod("code"); setErr(null); setPassword(""); }}>
            Código y PIN
          </button>
        </div>}

        <form onSubmit={(e) => void submit(e)} className="stack login-access-form">
          <label htmlFor="login-identity" className="login-field-label">{codeMode ? "Código de estudiante" : student ? "Correo electrónico" : "Correo"}</label>
          <div className="login-input-wrap">
            <Icon name={codeMode ? "shield" : "mail"}/>
            <input id="login-identity"
              type={codeMode ? "text" : "email"}
              value={codeMode ? code : email}
              onChange={(e) => codeMode ? setCode(e.target.value) : setEmail(e.target.value)}
              autoComplete="username"
              placeholder={codeMode ? "Código entregado por tu docente" : "Correo electrónico"}
              required/>
          </div>

          <label htmlFor="password" className="login-field-label">{codeMode ? "PIN" : "Contraseña"}</label>
          <div className="login-input-wrap password-field">
            <Icon name="lock"/>
            <input id="password" type={showPassword ? "text" : "password"}
              value={password} onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password" placeholder={codeMode ? "Tu PIN de acceso" : "Tu contraseña"} required/>
            <button type="button" className="password-toggle"
              aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}>
              <Icon name={showPassword ? "eye-off" : "eye"}/>
            </button>
          </div>

          <div className="login-preferences">
            <label className="login-remember">
              <input type="checkbox" checked={rememberEmail} onChange={(e) => setRememberEmail(e.target.checked)}/>
              <span>Recordarme</span>
            </label>
            <button type="button" className="login-forgot" aria-expanded={helpOpen}
              onClick={() => setHelpOpen(!helpOpen)}>¿Olvidaste tu contraseña?</button>
          </div>
          {helpOpen && <p className="login-recovery" role="status">
            {student ? "Solicita a tu docente que restablezca la contraseña o el PIN de tu cuenta." :
              "Solicita a la administración de tu institución que restablezca tu acceso."}
            {" "}Este formulario no envía correos automáticos.
          </p>}
          <ErrorBox message={err}/>
          <button type="submit" className="login-submit" disabled={busy}>
            {busy ? "Ingresando…" : "Ingresar"} <Icon name="arrow"/>
          </button>
        </form>

        <p className="login-help">¿Necesitas acceso? Contacta a la administración de tu institución.</p>
        <div className="login-footnote"><Icon name="students"/> Educación que acompaña a cada comunidad</div>
      </div>
    </section>
  </main>;
}
