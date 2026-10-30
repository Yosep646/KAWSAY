import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { hasStoredSession, login as apiLogin, studentLogin as apiStudentLogin, logout as apiLogout, restoreSession, setSessionLostHandler, setTokens } from "../services/api";
import type { UserBrief } from "../types/api";
import { offlineVault } from "../services/offlineVault";
import { pendingAttempts } from "../services/pendingAttempts";

interface AuthState { user: UserBrief | null; loading: boolean; onlineSession: boolean; login: (e: string, p: string) => Promise<void>; loginStudent: (code: string, pin: string) => Promise<void>; unlockOffline: (phrase: string) => Promise<void>; logout: () => Promise<void> }
const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserBrief | null>(null);
  const [loading, setLoading] = useState<boolean>(hasStoredSession());
  const [onlineSession, setOnlineSession] = useState(false);

  useEffect(() => {
    setSessionLostHandler(() => { offlineVault.lock(); setOnlineSession(false); setUser(null); });
    if (hasStoredSession()) {
      restoreSession().then(restored => { setUser(restored); setOnlineSession(Boolean(restored)); }).catch(() => setUser(null)).finally(() => setLoading(false));
    }
    return () => setSessionLostHandler(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const t = await apiLogin(email, password);
    if (t.user.role === "STUDENT") {   // el panel docente no es para estudiantes
      await apiLogout();
      throw new Error("Este panel es solo para docentes y administración");
    }
    offlineVault.lock(); setOnlineSession(true); setUser(t.user);
  }, []);
  const loginStudent = useCallback(async (code: string, pin: string) => {
    const localStudentId = offlineVault.isOpen() ? (await offlineVault.snapshot()).user.id : null;
    const key = "kawsay_web_device_id";
    let id = localStorage.getItem(key);
    if (!id) { id = crypto.randomUUID(); localStorage.setItem(key, id); }
    const t = await apiStudentLogin(code, pin, id);
    if (localStudentId && localStudentId !== t.user.id) {
      await apiLogout();
      throw new Error("Inicia sesión con la cuenta de las actividades descargadas, o bloquea primero el acceso local.");
    }
    setOnlineSession(true); setUser(t.user);
  }, []);
  const unlockOffline = useCallback(async (phrase: string) => {
    const local = await offlineVault.unlock(phrase);
    setTokens(null);
    setOnlineSession(false); setUser(local.user);
  }, []);
  const logout = useCallback(async () => {
    if (user?.role === "STUDENT" && typeof indexedDB !== "undefined" && await pendingAttempts.hasForStudent(user.id)) {
      throw new Error("Hay una respuesta de la vista en línea pendiente. Confírmala antes de salir.");
    }
    offlineVault.lock(); setOnlineSession(false); setUser(null); await apiLogout();
  }, [user]);
  const value = useMemo(() => ({ user, loading, onlineSession, login, loginStudent, unlockOffline, logout }), [user, loading, onlineSession, login, loginStudent, unlockOffline, logout]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth fuera de AuthProvider");
  return v;
}
