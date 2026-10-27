import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { hasStoredSession, login as apiLogin, studentLogin as apiStudentLogin, studentEmailLogin as apiStudentEmailLogin, logout as apiLogout, restoreSession, setSessionLostHandler } from "../services/api";
import type { UserBrief } from "../types/api";

interface AuthState { user: UserBrief | null; loading: boolean; login: (e: string, p: string) => Promise<void>; loginStudent: (code: string, pin: string) => Promise<void>; loginStudentEmail: (email: string, password: string) => Promise<void>; logout: () => Promise<void> }
const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserBrief | null>(null);
  const [loading, setLoading] = useState<boolean>(hasStoredSession());

  useEffect(() => {
    setSessionLostHandler(() => setUser(null));
    if (hasStoredSession()) {
      restoreSession().then(setUser).catch(() => setUser(null)).finally(() => setLoading(false));
    }
    return () => setSessionLostHandler(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const t = await apiLogin(email, password);
    if (t.user.role === "STUDENT") {   // el panel docente no es para estudiantes
      await apiLogout();
      throw new Error("Este panel es solo para docentes y administración");
    }
    setUser(t.user);
  }, []);
  const loginStudent = useCallback(async (code: string, pin: string) => {
    const key = "kawsay_web_device_id";
    let id = localStorage.getItem(key);
    if (!id) { id = crypto.randomUUID(); localStorage.setItem(key, id); }
    const t = await apiStudentLogin(code, pin, id);
    setUser(t.user);
  }, []);
  const loginStudentEmail = useCallback(async (email: string, password: string) => {
    const key = "kawsay_web_device_id";
    let deviceId: string | null = null;
    try { deviceId = localStorage.getItem(key); } catch { /* Storage restricted */ }
    if (!deviceId) {
      deviceId = crypto.randomUUID();
      try { localStorage.setItem(key, deviceId); } catch { /* Session-only device */ }
    }
    const token = await apiStudentEmailLogin(email, password, deviceId);
    if (token.user.role !== "STUDENT") { await apiLogout(); throw new Error("Esta cuenta no es de estudiante"); }
    setUser(token.user);
  }, []);
  const logout = useCallback(async () => { await apiLogout(); setUser(null); }, []);
  const value = useMemo(() => ({ user, loading, login, loginStudent, loginStudentEmail, logout }), [user, loading, login, loginStudent, loginStudentEmail, logout]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth fuera de AuthProvider");
  return v;
}
