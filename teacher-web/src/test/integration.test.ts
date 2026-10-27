// Prueba de integración REAL contra un backend KAWSAY en ejecución (VITE_API_URL). No usa mocks.
import { describe, expect, it } from "vitest";
import { api, login, setTokens } from "../services/api";
import type { Classroom, Summary, SupportFlag } from "../types/api";

const email = import.meta.env.VITE_TEST_TEACHER_EMAIL as string | undefined;
const password = import.meta.env.VITE_TEST_TEACHER_PASSWORD as string | undefined;
const maybe = email && password ? describe : describe.skip;

maybe("integración con el backend real", () => {
  it("login, aulas, resumen y alertas con evidencia llegan tipados desde el servidor", async () => {
    const t = await login(email as string, password as string);
    expect(t.user.role).toBe("TEACHER");
    const rooms = await api.get<Classroom[]>("/classrooms");
    expect(rooms.length).toBeGreaterThan(0);
    const room = rooms[0] as Classroom;
    const s = await api.get<Summary>(`/analytics/classrooms/${room.id}/summary`);
    expect(s.students_total).toBeGreaterThan(0);
    const flags = await api.get<SupportFlag[]>(`/support-flags?classroom_id=${room.id}`);
    expect(flags.length).toBeGreaterThan(0);
    const f = flags[0] as SupportFlag;
    expect(f.evidence.window).toBe(5);
    expect(f.evidence.difficult).toBeGreaterThanOrEqual(4);
    expect(f.message).toContain("Evidencia");
    // refresco automático: invalidar el access token en memoria y verificar que el cliente se recupera
    setTokens({ access_token: "invalido", refresh_token: sessionStorage.getItem("kawsay_rt") as string });
    expect((await api.get<Classroom[]>("/classrooms")).length).toBeGreaterThan(0);
  });
});
