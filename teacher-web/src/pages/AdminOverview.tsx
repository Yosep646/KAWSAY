import { useState } from "react";
import { Link } from "react-router-dom";
import { Icon, type IconName } from "../components/Icon";
import "./admin-overview.css";

type School = { id: string; name: string };
type Staff = { id: string; role: string; display_name: string; is_active: boolean };
type Audit = { id: string; action: string; target_type: string; created_at: string };
type Event = { id: string; type: string; status: string };

interface Props {
  schools: School[] | null;
  staff: Staff[] | null;
  audits: Audit[] | null;
  events: Event[] | null;
  loading: boolean;
  errors: string[];
  onRefresh: () => Promise<void>;
}

const shortcuts: { to: string; icon: IconName; title: string; description: string; tone: string }[] = [
  { to: "/admin/instituciones", icon: "classroom", title: "Instituciones", description: "Registra y organiza los colegios.", tone: "teal" },
  { to: "/admin/docentes", icon: "students", title: "Personal docente", description: "Gestiona cuentas y accesos.", tone: "blue" },
  { to: "/admin/curriculo", icon: "book", title: "Currículo", description: "Revisa los marcos de aprendizaje.", tone: "gold" },
  { to: "/admin/sistema", icon: "settings", title: "Sistema y auditoría", description: "Consulta los registros y eventos.", tone: "violet" },
];

function prettyDate(value: string): string {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "Fecha no disponible";
  return d.toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "numeric" });
}

export function AdminOverview({ schools, staff, audits, events, loading, errors, onRefresh }: Props) {
  const [query, setQuery] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const teacherCount = staff?.filter((u) => u.role === "TEACHER").length;
  const schoolPreview = schools?.filter((item) => item.name.toLocaleLowerCase("es").includes(query.trim().toLocaleLowerCase("es"))) ?? [];
  const summary: { label: string; value: number | undefined; detail: string; icon: IconName; to: string; tone: string }[] = [
    { label: "Instituciones", value: schools?.length, detail: "Registradas", icon: "classroom", to: "/admin/instituciones", tone: "teal" },
    { label: "Docentes", value: teacherCount, detail: "Cuentas registradas", icon: "students", to: "/admin/docentes", tone: "blue" },
    { label: "Eventos", value: events?.length, detail: "Últimos 20 consultados", icon: "activity", to: "/admin/sistema", tone: "gold" },
    { label: "Auditorías", value: audits?.length, detail: "Últimos 20 registros", icon: "check", to: "/admin/sistema", tone: "violet" },
  ];

  async function refresh() {
    if (refreshing) return;
    setRefreshing(true);
    try { await onRefresh(); }
    finally { setRefreshing(false); }
  }

  return (
    <div className="ka-overview">
      <section className="ka-home-hero" aria-labelledby="ka-home-title">
        <div className="ka-home-hero-content">
          <p className="ka-home-kicker"><span className="ka-home-kicker-dot" /> CENTRO DE ADMINISTRACIÓN <span>·</span> KAWSAY AI</p>
          <h1 id="ka-home-title">Un mejor panorama para <em>cada decisión.</em></h1>
          <p className="ka-home-intro">Gestiona tus instituciones, acompaña al equipo docente y mantén el control de tu plataforma educativa.</p>
          <div className="ka-home-hero-cta">
            <Link className="ka-home-primary" to="/admin/docentes"><Icon name="students" /> Registrar docente <Icon name="arrow" /></Link>
            <Link className="ka-home-secondary" to="/admin/instituciones">Ver instituciones <Icon name="arrow" /></Link>
          </div>
        </div>
        <div className="ka-home-hero-visual" aria-hidden="true">
          <div className="ka-home-orbit ka-home-orbit-one" />
          <div className="ka-home-orbit ka-home-orbit-two" />
          <div className="ka-home-brand-seal"><Icon name="leaf" /></div>
          <div className="ka-home-visual-tag"><span>KAWSAY</span><strong>Educación que acompaña</strong></div>
        </div>
      </section>

      <div className="ka-home-heading">
        <div><p className="ka-home-section-overline">TU PLATAFORMA EN CIFRAS</p><h2>Resumen general</h2><p>Datos consultados directamente del sistema.</p></div>
        <button className="ka-home-refresh" type="button" onClick={() => void refresh()} disabled={refreshing} aria-label="Actualizar los datos del panel">
          <Icon name="activity" /> {refreshing ? "Actualizando…" : "Actualizar datos"}
        </button>
      </div>

      {errors.length > 0 && <div className="ka-home-error" role="alert">Algunas consultas no se pudieron completar. Usa «Actualizar datos» para volver a intentarlo.</div>}

      <div className="ka-home-metrics" aria-label="Indicadores del sistema">
        {summary.map((metric) => (
          <Link className="ka-home-metric" to={metric.to} key={metric.label}>
            <div className="ka-home-metric-head">
              <span className={"ka-home-metric-icon ka-tone-" + metric.tone}><Icon name={metric.icon} /></span>
              <Icon name="arrow" />
            </div>
            <strong>{metric.value ?? (loading ? "…" : "—")}</strong>
            <div><span>{metric.label}</span><small>{metric.detail}</small></div>
          </Link>
        ))}
      </div>

      <div className="ka-home-main-grid">
        <section className="ka-home-panel ka-home-shortcuts" aria-labelledby="ka-quick-actions">
          <div className="ka-home-panel-heading"><div><p className="ka-home-section-overline">ACCESOS DIRECTOS</p><h2 id="ka-quick-actions">¿Qué quieres gestionar?</h2></div><span className="ka-home-heading-mark"><Icon name="spark" /></span></div>
          <div className="ka-home-shortcut-grid">
            {shortcuts.map((item) => <Link to={item.to} key={item.to} className="ka-home-shortcut">
              <span className={"ka-home-shortcut-icon ka-tone-" + item.tone}><Icon name={item.icon} /></span>
              <strong>{item.title}</strong>
              <p>{item.description}</p>
              <span className="ka-home-shortcut-arrow"><Icon name="arrow" /></span>
            </Link>)}
          </div>
        </section>
        <section className="ka-home-panel ka-home-activity" aria-labelledby="ka-recent-activity">
          <div className="ka-home-panel-heading"><div><p className="ka-home-section-overline">SEGUIMIENTO</p><h2 id="ka-recent-activity">Actividad reciente</h2></div><span className="ka-home-activity-icon"><Icon name="activity" /></span></div>
          <p className="ka-home-panel-description">Últimos registros de auditoría disponibles.</p>
          <div className="ka-home-timeline">
            {(audits ?? []).slice(0, 4).map((item) =>
              <div className="ka-home-timeline-event" key={item.id}>
                <span className="ka-home-timeline-dot" aria-hidden="true" />
                <div><strong>{item.action}</strong><p>{item.target_type} <span>· {prettyDate(item.created_at)}</span></p></div>
              </div>
            )}
            {audits?.length === 0 && <div className="ka-home-empty"><Icon name="check" /><p>Aún no hay movimientos registrados en la auditoría.</p></div>}
            {!audits && <div className="ka-home-empty"><p>{loading ? "Consultando actividad…" : "La actividad no está disponible."}</p></div>}
          </div>
          <Link className="ka-home-panel-link" to="/admin/sistema">Consultar auditoría <Icon name="arrow" /></Link>
        </section>
      </div>

      <section className="ka-home-panel ka-home-schools" aria-labelledby="ka-institutions">
        <div className="ka-home-schools-heading">
          <div><p className="ka-home-section-overline">RED EDUCATIVA</p><h2 id="ka-institutions">Instituciones registradas</h2><p>Explora las instituciones existentes en tu plataforma.</p></div>
          <Link className="ka-home-panel-link" to="/admin/instituciones">Ver todas <Icon name="arrow" /></Link>
        </div>
        <div className="ka-home-schools-toolbar">
          <label htmlFor="ka-school-search">Buscar institución
            <input id="ka-school-search" type="search" placeholder="Escribe el nombre de una institución…" value={query} onChange={(e) => setQuery(e.target.value)} />
          </label>
          <span>{schoolPreview.length} {schoolPreview.length === 1 ? "resultado" : "resultados"}</span>
        </div>
        <div className="ka-home-school-list">
          {schoolPreview.slice(0, 6).map((item) => (
            <div className="ka-home-school-row" key={item.id}>
              <span className="ka-home-school-icon"><Icon name="classroom" /></span>
              <div><strong>{item.name}</strong><small>Institución educativa</small></div>
              <Link to="/admin/instituciones" aria-label={"Gestionar " + item.name}><Icon name="arrow" /></Link>
            </div>
          ))}
          {schools && schoolPreview.length === 0 && <p className="ka-home-school-empty">{query.trim() ? "No se encontraron instituciones con ese nombre." : "Aún no hay instituciones registradas."}</p>}
          {!schools && <p className="ka-home-school-empty">{loading ? "Cargando instituciones…" : "No se pudo cargar la lista."}</p>}
        </div>
        {schoolPreview.length > 6 && <Link className="ka-home-more" to="/admin/instituciones">Ver las {schoolPreview.length} instituciones <Icon name="arrow" /></Link>}
      </section>
    </div>
  );
}
