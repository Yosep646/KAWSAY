import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, api, hasStoredSession, login, restoreSession, setSessionLostHandler, setTokens } from "../services/api";

const json = (status: number, body: unknown) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
const tokens = (a: string, r: string) => ({ access_token: a, refresh_token: r, expires_in: 900, user: { id: "u1", role: "TEACHER", display_name: "Doc" } });

describe("api client", () => {
  beforeEach(() => { sessionStorage.clear(); setTokens(null); });
  afterEach(() => { vi.restoreAllMocks(); setSessionLostHandler(null); });

  it("login guarda el refresh en sessionStorage y envía el access token en memoria", async () => {
    const f = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(200, tokens("A1", "R1"))).mockResolvedValueOnce(json(200, []));
    await login("a@b.pe", "x");
    expect(sessionStorage.getItem("kawsay_rt")).toBe("R1");
    expect(localStorage.length).toBe(0);                       // nada de tokens en localStorage
    await api.get("/classrooms");
    const headers = (f.mock.calls[1]?.[1] as RequestInit).headers as Record<string, string>;
    expect(headers.authorization).toBe("Bearer A1");
  });

  it("ante 401 refresca UNA vez, rota el token y reintenta la petición", async () => {
    setTokens({ access_token: "OLD", refresh_token: "R1" });
    const f = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json(401, { code: "unauthorized", message: "x" }))
      .mockResolvedValueOnce(json(200, tokens("NEW", "R2")))
      .mockResolvedValueOnce(json(200, [{ id: "c1" }]));
    const out = await api.get<{ id: string }[]>("/classrooms");
    expect(out).toEqual([{ id: "c1" }]);
    expect(sessionStorage.getItem("kawsay_rt")).toBe("R2");
    expect(f).toHaveBeenCalledTimes(3);
    expect(((f.mock.calls[2]?.[1] as RequestInit).headers as Record<string, string>).authorization).toBe("Bearer NEW");
  });

  it("si el refresh falla, cierra la sesión y avisa", async () => {
    setTokens({ access_token: "OLD", refresh_token: "R1" });
    const lost = vi.fn();
    setSessionLostHandler(lost);
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(401, { code: "unauthorized", message: "x" })).mockResolvedValueOnce(json(401, { code: "unauthorized", message: "x" }));
    await expect(api.get("/classrooms")).rejects.toBeInstanceOf(ApiError);
    expect(lost).toHaveBeenCalled();
    expect(hasStoredSession()).toBe(false);
  });

  it("expone código, mensaje y request_id del error del servidor", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(409, { code: "conflict", message: "Ya existe", request_id: "rid-1" }));
    await expect(api.post("/classrooms", {})).rejects.toMatchObject({ status: 409, code: "conflict", message: "Ya existe", requestId: "rid-1" });
  });

  it("restoreSession devuelve null sin refresh token", async () => {
    expect(await restoreSession()).toBeNull();
  });

  it("conserva la sesión cuando el refresh falla temporalmente", async () => {
    setTokens({ access_token: "OLD", refresh_token: "R1" });
    const lost = vi.fn();
    setSessionLostHandler(lost);
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(401, {})).mockResolvedValueOnce(json(503, { message: "No disponible" }));
    await expect(api.get("/classrooms")).rejects.toMatchObject({ status: 503 });
    expect(hasStoredSession()).toBe(true);
    expect(lost).not.toHaveBeenCalled();
  });

  it("clasifica HTML inesperado sin mostrar su contenido", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response("<html>proxy</html>", { status: 502 }));
    await expect(api.get("/classrooms")).rejects.toMatchObject({ status: 502, code: "invalid_response" });
  });

  it("interrumpe peticiones lentas con un error comprensible", async () => {
    vi.useFakeTimers();
    try {
      vi.spyOn(globalThis, "fetch").mockImplementation((_url, init) => new Promise((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
      }));
      const result = expect(api.get("/classrooms", { timeoutMs: 20 })).rejects.toMatchObject({ code: "timeout" });
      await vi.advanceTimersByTimeAsync(20);
      await result;
    } finally { vi.useRealTimers(); }
  });

  it("propaga cancelación explícita", async () => {
    const controller = new AbortController();
    vi.spyOn(globalThis, "fetch").mockImplementation((_url, init) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
    }));
    const result = expect(api.get("/classrooms", { signal: controller.signal })).rejects.toMatchObject({ name: "AbortError" });
    controller.abort();
    await result;
  });
});
