import type { TokenOut } from "../types/api";

const BASE: string = (import.meta.env.VITE_API_URL as string | undefined) ?? "";
const API = `${BASE}/api/v1`;
const RT_KEY = "kawsay_rt";
const sessionStore = {
  getItem(key: string): string | null { try { return window.sessionStorage.getItem(key); } catch { return null; } },
  setItem(key: string, value: string): void { try { window.sessionStorage.setItem(key, value); } catch { /* Storage disabled: continue without persisted session. */ } },
  removeItem(key: string): void { try { window.sessionStorage.removeItem(key); } catch { /* Ignore blocked storage. */ } },
};

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public requestId?: string) {
    super(message);
  }
}

// El access token vive SOLO en memoria. El refresh token se guarda en sessionStorage (se borra al cerrar la pestaña).
// Trade-off documentado en docs/14-security.md: una cookie httpOnly sería más segura y queda como mejora.
let accessToken: string | null = null;
let refreshing: Promise<boolean> | null = null;
let onSessionLost: (() => void) | null = null;

export function setSessionLostHandler(fn: (() => void) | null): void {
  onSessionLost = fn;
}
export function setTokens(t: Pick<TokenOut, "access_token" | "refresh_token"> | null): void {
  accessToken = t?.access_token ?? null;
  if (t) sessionStore.setItem(RT_KEY, t.refresh_token);
  else sessionStore.removeItem(RT_KEY);
}
export function hasStoredSession(): boolean {
  return sessionStore.getItem(RT_KEY) !== null;
}

async function parse<T>(res: Response): Promise<T> {
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  let data: unknown;
  try {
    data = text ? JSON.parse(text) : undefined;
  } catch {
    throw new ApiError(res.status, "invalid_response", "El servidor devolvió una respuesta inválida. Inténtalo de nuevo.");
  }
  if (!res.ok) {
    const d = (data ?? {}) as { code?: string; message?: string; request_id?: string };
    throw new ApiError(res.status, d.code ?? "error", d.message ?? `Error ${res.status}`, d.request_id);
  }
  return data as T;
}

export interface RequestOptions { signal?: AbortSignal; timeoutMs?: number }

async function fetchWithTimeout(url: string, init: RequestInit, options: RequestOptions = {}): Promise<Response> {
  const controller = new AbortController();
  const cancel = () => controller.abort(options.signal?.reason);
  if (options.signal?.aborted) cancel();
  options.signal?.addEventListener("abort", cancel, { once: true });
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, options.timeoutMs ?? 15000);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new ApiError(0, timedOut ? "timeout" : "network_error", timedOut
      ? "El servidor tardó demasiado en responder. Inténtalo de nuevo."
      : "No se pudo conectar con el servidor. Comprueba tu conexión.");
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", cancel);
  }
}

async function refreshTokens(): Promise<boolean> {
  const rt = sessionStore.getItem(RT_KEY);
  if (!rt) return false;
  refreshing ??= (async () => {
    try {
      const res = await fetchWithTimeout(`${API}/auth/refresh`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ refresh_token: rt }) });
      if (res.status === 401) return false;
      setTokens(await parse<TokenOut>(res));
      return true;
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

export async function request<T>(method: string, path: string, body?: unknown, retry = true, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["content-type"] = "application/json";
  if (accessToken) headers.authorization = `Bearer ${accessToken}`;
  const res = await fetchWithTimeout(`${API}${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) }, options);
  if (res.status === 401 && retry && !path.startsWith("/auth/")) {
    if (await refreshTokens()) return request<T>(method, path, body, false, options);
    setTokens(null);
    onSessionLost?.();
  }
  return parse<T>(res);
}

export const api = {
  get: <T>(p: string, options?: RequestOptions) => request<T>("GET", p, undefined, true, options),
  post: <T>(p: string, b?: unknown) => request<T>("POST", p, b ?? {}),
  put: <T>(p: string, b: unknown) => request<T>("PUT", p, b),
  patch: <T>(p: string, b: unknown) => request<T>("PATCH", p, b),
};

export async function login(email: string, password: string): Promise<TokenOut> {
  const t = await request<TokenOut>("POST", "/auth/login", { email, password });
  setTokens(t);
  return t;
}
export async function studentLogin(loginCode: string, pin: string, deviceId: string): Promise<TokenOut> {
  const t = await request<TokenOut>("POST", "/auth/student-login", { login_code: loginCode, pin, device_id: deviceId });
  setTokens(t);
  return t;
}
export async function restoreSession(): Promise<TokenOut["user"] | null> {
  if (!(await refreshTokens())) return null;
  return request<TokenOut["user"]>("GET", "/auth/me");
}
export async function logout(): Promise<void> {
  const rt = sessionStore.getItem(RT_KEY);
  setTokens(null);
  if (rt) await fetchWithTimeout(`${API}/auth/logout`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ refresh_token: rt }) }).catch(() => undefined);
}
