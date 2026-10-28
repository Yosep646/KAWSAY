import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CreateAssignment } from "../pages/Assignments";
import * as svc from "../services/api";

beforeEach(() => window.sessionStorage.clear());
afterEach(() => vi.restoreAllMocks());

describe("Creación de ejercicios cuando falta planificación", () => {
  it("explica el bloqueo real y conserva la actividad escrita al regresar de planificación", async () => {
    vi.spyOn(svc.api,"get").mockImplementation(async (path: string) => {
      if (path === "/classrooms") return [{id:"room-1",name:"Aula 1",school_id:"school-1",academic_year:2026}];
      if (path === "/curriculum/grades") return [];
      if (path === "/planning/plans") return [];
      if (path.startsWith("/planning/active?classroom_id=")) return [];
      throw new Error("Consulta no prevista: "+path);
    });
    const first = render(<MemoryRouter><CreateAssignment/></MemoryRouter>);
    await screen.findByRole("textbox", {name:/Título de la actividad/});
    await waitFor(() => expect(screen.getByText(/Falta activar una planificación curricular/)).toBeInTheDocument());
    const create = screen.getByRole("button",{name:/Crear variantes para revisión/});
    expect(create).toBeDisabled();
    const title = screen.getByRole("textbox",{name:/Título de la actividad/});
    const instructions = screen.getByRole("textbox",{name:/Actividad base/});
    await userEvent.type(title,"Suma de números naturales");
    await userEvent.type(instructions,"Resolver sumas con ejemplos de mi comunidad.");
    expect(create).toBeDisabled();
    await waitFor(()=>expect(window.sessionStorage.getItem("kawsay.teacher.exercise-draft.v1"))
      .toContain("Suma de números naturales"));
    expect(screen.getByRole("link",{name:/Continuar con planificación/}))
      .toHaveAttribute("href","/planificacion#crear-plan-estructurado");
    first.unmount();
    render(<MemoryRouter><CreateAssignment/></MemoryRouter>);
    expect(screen.getByRole("textbox",{name:/Título de la actividad/})).toHaveValue("Suma de números naturales");
    expect(screen.getByRole("textbox",{name:/Actividad base/})).toHaveValue("Resolver sumas con ejemplos de mi comunidad.");
  });
});
