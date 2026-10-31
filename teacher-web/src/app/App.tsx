import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useState, type ReactNode } from "react";
import { Admin } from "../pages/Admin";
import { Alerts } from "../pages/Alerts";
import { AssignmentList, AssignmentReview, CreateAssignment } from "../pages/Assignments";
import { Classrooms } from "../pages/Classrooms";
import { Dashboard } from "../pages/Dashboard";
import { Login } from "../pages/Login";
import { Planning } from "../pages/Planning";
import { Students } from "../pages/Students";
import { StudentHome } from "../pages/StudentHome";
import { StudentActivity } from "../pages/StudentActivity";
import { StudentLanguageSettings } from "../pages/StudentLanguageSettings";
import { StudentTutor } from "../pages/StudentTutor";
import { AuthProvider, useAuth } from "./AuthContext";
import type { Role } from "../types/api";
import { Brand, Icon, type IconName } from "../components/Icon";

const teacherLinks: { to: string; label: string; icon: IconName }[] = [
  { to: "/", label: "Dashboard", icon: "dashboard" },
  { to: "/aulas", label: "Mis aulas", icon: "classroom" },
  { to: "/estudiantes", label: "Estudiantes", icon: "students" },
  { to: "/planificacion", label: "Planificación", icon: "book" },
  { to: "/actividades", label: "Actividades", icon: "tasks" },
  { to: "/alertas", label: "Alertas educativas", icon: "alert" },
];
const adminLinks: typeof teacherLinks = [
  { to: "/admin", label: "Panel general", icon: "dashboard" },
  { to: "/admin/instituciones", label: "Instituciones", icon: "classroom" },
  { to: "/admin/docentes", label: "Docentes", icon: "students" },
  { to: "/admin/estudiantes", label: "Estudiantes", icon: "graduation" },
  { to: "/admin/curriculo", label: "Currículo y contenidos", icon: "book" },
  { to: "/admin/tareas", label: "Asignaciones y tareas", icon: "tasks" },
  { to: "/admin/reportes", label: "Reportes de aprendizaje", icon: "chart" },
  { to: "/admin/sistema", label: "Auditoría y registros", icon: "shield" },
  { to: "/admin/usuarios", label: "Usuarios y roles", icon: "students" },
  { to: "/admin/configuracion", label: "Configuración", icon: "settings" },
  { to: "/admin/respaldos", label: "Respaldos", icon: "database" },
];
const studentLinks: typeof teacherLinks = [
  { to: "/estudiante", label: "Mi inicio", icon: "dashboard" },
  { to: "/estudiante/cursos", label: "Mis cursos", icon: "book" },
  { to: "/estudiante/actividades", label: "Mis actividades", icon: "tasks" },
  { to: "/estudiante/tutor", label: "Tutor IA", icon: "spark" },
  { to: "/estudiante/progreso", label: "Mi progreso", icon: "activity" },
  { to: "/estudiante/idioma", label: "Mi idioma", icon: "settings" },
];

function Protected({ roles, children }: { roles?: Role[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="muted">Cargando…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <p role="alert" className="error">No tienes permiso para ver esta sección.</p>;
  return <>{children}</>;
}

function Shell() {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [adminSearch, setAdminSearch] = useState("");
  const [adminLight, setAdminLight] = useState(false);
  const [sidebarCompact, setSidebarCompact] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const matchedLinks = adminSearch.trim() ? adminLinks.filter(l=>l.label.toLocaleLowerCase("es").includes(adminSearch.trim().toLocaleLowerCase("es"))) : [];
  const links = user?.role === "ADMIN" ? adminLinks : user?.role === "STUDENT" ? studentLinks : teacherLinks;
  const section = [...links].sort((a,b) => b.to.length - a.to.length).find((link) => link.to === "/" ? pathname === "/" : (pathname === link.to || pathname.startsWith(link.to + "/")))?.label ?? "Panel";
  const initials = user?.display_name.trim().split(/\s+/).slice(0, 2).map((word) => word[0]).join("").toUpperCase();
  return (
    <div className={`shell role-${user?.role.toLowerCase()} ${adminLight && user?.role==="ADMIN" ? "admin-sun-mode" : ""} ${sidebarCompact && user?.role==="ADMIN" ? "sidebar-compact" : ""} ${mobileNavOpen ? "mobile-nav-open" : ""}`}>
      <a className="skip-link" href="#contenido">Saltar al contenido</a>
      <aside className="sidebar">
        <Brand />
        <button type="button" className="mobile-nav-toggle" aria-controls="kawsay-primary-nav"
          aria-expanded={mobileNavOpen} aria-label={mobileNavOpen ? "Cerrar menú principal" : "Abrir menú principal"}
          onClick={() => setMobileNavOpen((open) => !open)}>
          <Icon name={mobileNavOpen ? "x" : "menu"} /> <span>{mobileNavOpen ? "Cerrar" : "Menú"}</span>
        </button>
        {user?.role !== "ADMIN" && <p className="nav-caption">ESPACIO DE {user?.role === "STUDENT" ? "APRENDIZAJE" : "DOCENCIA"}</p>}
        <nav id="kawsay-primary-nav" aria-label="Principal" className="primary-nav">
          {links.map((link, index) => <div className="admin-nav-group" key={link.to}>
            {user?.role === "ADMIN" && index === 1 && <p className="nav-caption">GESTIÓN ACADÉMICA</p>}
            {user?.role === "ADMIN" && index === 7 && <p className="nav-caption">SISTEMA</p>}
            <NavLink to={link.to} end={link.to === "/" || link.to === "/admin"} onClick={() => setMobileNavOpen(false)}><Icon name={link.icon} /><span>{link.label}</span></NavLink>
          </div>)}
        </nav>
        <div className="sidebar-note"><Icon name="leaf" /><strong>Cada estudiante cuenta.</strong><p>La evidencia orienta.<br />Tú decides cómo acompañar.</p></div>
        <div className="sidebar-footer">KAWSAY AI <span>·</span> Aula multigrado</div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          {user?.role === "ADMIN" ? <div className="admin-header">
            <div className="admin-header-start">
              <button type="button" className="admin-header-icon admin-menu-btn" aria-label={sidebarCompact?"Expandir menú":"Contraer menú"} onClick={()=>setSidebarCompact(!sidebarCompact)}><Icon name="menu" /></button>
              <div className="admin-header-search">
                <Icon name="search" />
                <input type="search" aria-label="Buscar secciones de administración" placeholder="Buscar instituciones, docentes, estudiantes…" value={adminSearch}
                  onChange={e=>setAdminSearch(e.target.value)} onKeyDown={e=>{if(e.key==="Enter" && matchedLinks.length){navigate(matchedLinks[0]?.to ?? "/admin");setAdminSearch("");}}}/>
                {adminSearch.trim() && <div className="admin-search-results" role="region" aria-label="Resultados de búsqueda">
                  {matchedLinks.length? matchedLinks.map(l=><NavLink to={l.to} key={l.to} onClick={()=>setAdminSearch("")}><Icon name={l.icon}/>{l.label}</NavLink>) :
                  <span className="admin-search-empty">No hay secciones con ese nombre.</span>}
                </div>}
              </div>
            </div>
            <div className="admin-header-actions">
              <button type="button" className="admin-header-icon" aria-label={adminLight?"Activar modo oscuro":"Activar modo claro"} aria-pressed={adminLight} onClick={()=>setAdminLight(!adminLight)}><Icon name={adminLight?"moon":"sun"} /></button>
              <NavLink to="/admin/sistema" className="admin-header-icon" aria-label="Ver auditoría y eventos"><Icon name="bell"/></NavLink>
              <div className="account"><span className="avatar" aria-hidden="true">{initials}</span><div className="account-name"><strong>{user?.display_name}</strong><small>Administración</small></div><button className="ghost logout" onClick={() => void logout()}><Icon name="logout" />Salir</button></div>
            </div>
          </div> : <>
          <div className="breadcrumb"><span>Mi espacio</span><span aria-hidden="true">/</span><strong>{section}</strong></div>
          <div className="account"><span className="avatar" aria-hidden="true">{initials}</span><div className="account-name"><strong>{user?.display_name}</strong><small>{user?.role === "STUDENT" ? "Estudiante" : "Docente"}</small></div><button className="ghost logout" onClick={() => void logout()}><Icon name="logout" />Salir</button></div>
          </>}
        </header>
      <main id="contenido" className="main-content" tabIndex={-1}>
        <Routes>
          <Route path="/" element={user?.role === "ADMIN" ? <Navigate to="/admin" replace /> : user?.role === "STUDENT" ? <Navigate to="/estudiante" replace /> : <Dashboard />} />
          <Route path="/docente" element={<Protected roles={["TEACHER"]}><Dashboard /></Protected>} />
          <Route path="/estudiante" element={<Protected roles={["STUDENT"]}><StudentHome /></Protected>} />
          <Route path="/estudiante/cursos" element={<Protected roles={["STUDENT"]}><StudentHome focus="courses" /></Protected>} />
          <Route path="/estudiante/actividades" element={<Protected roles={["STUDENT"]}><StudentHome focus="activities" /></Protected>} />
          <Route path="/estudiante/progreso" element={<Protected roles={["STUDENT"]}><StudentHome focus="progress" /></Protected>} />
          <Route path="/estudiante/idioma" element={<Protected roles={["STUDENT"]}><StudentLanguageSettings /></Protected>} />
          <Route path="/estudiante/tutor" element={<Protected roles={["STUDENT"]}><StudentTutor /></Protected>} />
          <Route path="/estudiante/actividad/:id" element={<Protected roles={["STUDENT"]}><StudentActivity /></Protected>} />
          <Route path="/aulas" element={<Protected roles={["TEACHER"]}><Classrooms /></Protected>} />
          <Route path="/estudiantes" element={<Protected roles={["TEACHER"]}><Students /></Protected>} />
          <Route path="/planificacion" element={<Protected roles={["TEACHER", "ADMIN"]}><Planning /></Protected>} />
          <Route path="/actividades" element={<Protected roles={["TEACHER"]}><AssignmentList /></Protected>} />
          <Route path="/actividades/nueva" element={<Protected roles={["TEACHER"]}><CreateAssignment /></Protected>} />
          <Route path="/actividades/:id" element={<Protected roles={["TEACHER"]}><AssignmentReview /></Protected>} />
          <Route path="/alertas" element={<Protected roles={["TEACHER"]}><Alerts /></Protected>} />
          <Route path="/admin" element={<Protected roles={["ADMIN"]}><Admin section="overview" /></Protected>} />
          <Route path="/admin/instituciones" element={<Protected roles={["ADMIN"]}><Admin section="schools" /></Protected>} />
          <Route path="/admin/docentes" element={<Protected roles={["ADMIN"]}><Admin section="teachers" /></Protected>} />
          <Route path="/admin/curriculo" element={<Protected roles={["ADMIN"]}><Admin section="curriculum" /></Protected>} />
          <Route path="/admin/sistema" element={<Protected roles={["ADMIN"]}><Admin section="system" /></Protected>} />
          <Route path="/admin/estudiantes" element={<Protected roles={["ADMIN"]}><Admin section="students" /></Protected>} />
          <Route path="/admin/tareas" element={<Protected roles={["ADMIN"]}><Admin section="tasks" /></Protected>} />
          <Route path="/admin/reportes" element={<Protected roles={["ADMIN"]}><Admin section="reports" /></Protected>} />
          <Route path="/admin/usuarios" element={<Protected roles={["ADMIN"]}><Admin section="users" /></Protected>} />
          <Route path="/admin/configuracion" element={<Protected roles={["ADMIN"]}><Admin section="configuration" /></Protected>} />
          <Route path="/admin/respaldos" element={<Protected roles={["ADMIN"]}><Admin section="backups" /></Protected>} />
          <Route path="*" element={<p>Página no encontrada.</p>} />
        </Routes>
      </main>
      <footer className="workspace-footer">Aprender a su ritmo. Acompañar con evidencia.<span>KAWSAY AI</span></footer>
      </div>
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={<Protected><Shell /></Protected>} />
      </Routes>
    </AuthProvider>
  );
}
