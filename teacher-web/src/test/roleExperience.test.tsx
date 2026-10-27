import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../app/AuthContext";
import { Admin } from "../pages/Admin";
import { Dashboard } from "../pages/Dashboard";
import { StudentHome } from "../pages/StudentHome";
import * as svc from "../services/api";

afterEach(() => vi.restoreAllMocks());

describe("Experiencia por rol KAWSAY", () => {
  it("el docente sin aulas conserva un acceso visible para crear su primera aula y registrar estudiantes", async () => {
    vi.spyOn(svc.api, "get").mockImplementation(async () => []);
    render(<MemoryRouter><Dashboard /></MemoryRouter>);
    expect(screen.getAllByRole("link", { name: /Registrar estudiante/ }).some(link => link.getAttribute("href") === "/estudiantes")).toBe(true);
    expect(await screen.findByRole("link", { name: /Crear mi primera aula/ })).toHaveAttribute("href", "/aulas");
    await waitFor(() => expect(screen.getByText(/Para agregar estudiantes y asignar tareas/)).toBeInTheDocument());
  });

  it("el estudiante ve indicadores procedentes de sus actividades y progreso, no valores de ejemplo", async () => {
    vi.spyOn(svc.api, "get").mockImplementation(async (path: string) => {
      if (path.includes("/sync/pull")) return {tasks:[{
        student_assignment_id:"a-1",title:"Lectura rural",subject:"Comunicación",
        instructions:"Lee atentamente las indicaciones."
      }],has_more:false,cursor:1};
      if (path === "/progress/me") return [{competency:"Comprensión lectora",percent:75}];
      throw new Error("Ruta inesperada");
    });
    render(<MemoryRouter><AuthProvider><StudentHome /></AuthProvider></MemoryRouter>);
    const activitiesLink = await screen.findByRole("link", { name: /Actividades asignadas/ });
    expect(within(activitiesLink).getByText("1")).toBeInTheDocument();
    expect(await screen.findByText("75 % de progreso")).toBeInTheDocument();
    expect(screen.getByText("Lectura rural")).toBeInTheDocument();
  });

  it("la administración filtra instituciones y dispone del formulario para crearlas", async () => {
    vi.spyOn(svc.api, "get").mockImplementation(async (path: string) => {
      if (path === "/schools") return [
        {id:"s1",name:"Colegio de Chupán"},{id:"s2",name:"Escuela de Cayhuayna"}
      ];
      if (path === "/users?limit=100") return [];
      if (path.startsWith("/audit-log") || path.startsWith("/automation/events")) return [];
      if (path === "/analytics/admin/overview") return null;
      throw new Error("Ruta inesperada");
    });
    render(<MemoryRouter><AuthProvider><Admin section="schools" /></AuthProvider></MemoryRouter>);
    await screen.findByText("Colegio de Chupán");
    await userEvent.type(screen.getByLabelText("Buscar institución"), "Cayhuayna");
    expect(screen.queryByText("Colegio de Chupán")).not.toBeInTheDocument();
    expect(screen.getByText("Escuela de Cayhuayna")).toBeInTheDocument();
    expect(screen.getByRole("button", {name:/Crear institución/})).toBeEnabled();
  });
});
