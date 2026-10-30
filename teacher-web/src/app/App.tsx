import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
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
import { OfflineActivity } from "../pages/OfflineActivity";
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
const adminLinks: typeof teacherLinks = [teacherLinks[3]!, { to: "/admin", label: "Administración", icon: "settings" }];
const studentLinks: typeof teacherLinks = [{ to: "/estudiante", label: "Mi inicio", icon: "dashboard" }];

function Protected({ roles, children }: { roles?: Role[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="muted">Cargando…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <p role="alert" className="error">No tienes permiso para ver esta sección.</p>;
  return <>{children}</>;
}

function Shell() {
  const { user, logout } = useAuth();
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const { pathname } = useLocation();
  const links = user?.role === "ADMIN" ? adminLinks : user?.role === "STUDENT" ? studentLinks : teacherLinks;
  const section = links.find((link) => link.to === "/" ? pathname === "/" : pathname.startsWith(link.to))?.label ?? "Panel";
  const initials = user?.display_name.trim().split(/\s+/).slice(0, 2).map((word) => word[0]).join("").toUpperCase();
  return (
    <div className={`shell role-${user?.role.toLowerCase()}`}>
      <a className="skip-link" href="#contenido">Saltar al contenido</a>
      <aside className="sidebar">
        <Brand />
        <p className="nav-caption">ESPACIO DE {user?.role === "ADMIN" ? "ADMINISTRACIÓN" : user?.role === "STUDENT" ? "APRENDIZAJE" : "DOCENCIA"}</p>
        <nav aria-label="Principal" className="primary-nav">
          {links.map((link) => <NavLink key={link.to} to={link.to} end={link.to === "/"}><Icon name={link.icon} /><span>{link.label}</span></NavLink>)}
        </nav>
        <div className="sidebar-note"><Icon name="leaf" /><strong>Cada estudiante cuenta.</strong><p>La evidencia orienta.<br />Tú decides cómo acompañar.</p></div>
        <div className="sidebar-footer">KAWSAY AI <span>·</span> Aula multigrado</div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb"><span>Mi espacio</span><span aria-hidden="true">/</span><strong>{section}</strong></div>
          <div className="account"><span className="avatar" aria-hidden="true">{initials}</span><div className="account-name"><strong>{user?.display_name}</strong><small>{user?.role === "ADMIN" ? "Administración" : user?.role === "STUDENT" ? "Estudiante" : "Docente"}</small></div><button className="ghost logout" onClick={() => void logout().catch(e => setLogoutError(e instanceof Error ? e.message : "No se pudo cerrar la sesión."))}><Icon name="logout" />Salir</button></div>
        </header>
      <main id="contenido" className="main-content" tabIndex={-1}>
        {logoutError && <p role="alert" className="error">{logoutError}</p>}
        <Routes>
          <Route path="/" element={user?.role === "ADMIN" ? <Navigate to="/admin" replace /> : user?.role === "STUDENT" ? <Navigate to="/estudiante" replace /> : <Dashboard />} />
          <Route path="/docente" element={<Protected roles={["TEACHER"]}><Dashboard /></Protected>} />
          <Route path="/estudiante" element={<Protected roles={["STUDENT"]}><StudentHome /></Protected>} />
          <Route path="/estudiante/actividad/:id" element={<Protected roles={["STUDENT"]}><StudentActivity /></Protected>} />
          <Route path="/estudiante/descargada/:id" element={<Protected roles={["STUDENT"]}><OfflineActivity /></Protected>} />
          <Route path="/aulas" element={<Protected roles={["TEACHER"]}><Classrooms /></Protected>} />
          <Route path="/estudiantes" element={<Protected roles={["TEACHER"]}><Students /></Protected>} />
          <Route path="/planificacion" element={<Protected roles={["TEACHER", "ADMIN"]}><Planning /></Protected>} />
          <Route path="/actividades" element={<Protected roles={["TEACHER"]}><AssignmentList /></Protected>} />
          <Route path="/actividades/nueva" element={<Protected roles={["TEACHER"]}><CreateAssignment /></Protected>} />
          <Route path="/actividades/:id" element={<Protected roles={["TEACHER"]}><AssignmentReview /></Protected>} />
          <Route path="/alertas" element={<Protected roles={["TEACHER"]}><Alerts /></Protected>} />
          <Route path="/admin" element={<Protected roles={["ADMIN"]}><Admin /></Protected>} />
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
