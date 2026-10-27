import { useState } from "react";
import { FlagCard } from "../components/FlagCard";
import { ErrorBox, Loading } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import type { SupportFlag } from "../types/api";

const FILTERS = [["", "Todas"], ["OPEN", "Nuevas"], ["ACKNOWLEDGED", "En seguimiento"], ["RESOLVED", "Resueltas"], ["DISMISSED", "Descartadas"]] as const;

export function Alerts() {
  const [status, setStatus] = useState("");
  const flags = useAsync(() => api.get<SupportFlag[]>(`/support-flags${status ? `?status=${status}` : ""}`), [status]);
  return (
    <div>
      <h2>Alertas educativas</h2>
      <p className="muted">KAWSAY muestra la evidencia que hay detrás de cada alerta. No son diagnósticos: tú decides cómo acompañar.</p>
      <div className="row">{FILTERS.map(([v, l]) => <button key={v} className={status === v ? "" : "ghost"} onClick={() => setStatus(v)}>{l}</button>)}</div>
      <ErrorBox message={flags.error} />
      {flags.loading ? <Loading /> : (flags.data?.length ?? 0) === 0 ? <p className="muted">No hay alertas con este filtro.</p> : flags.data?.map((f) => <FlagCard key={f.id} flag={f} onChanged={() => void flags.reload()} />)}
    </div>
  );
}
