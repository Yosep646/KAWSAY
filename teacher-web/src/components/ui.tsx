import type { ReactNode } from "react";

export const Card = ({ title, children, actions }: { title?: string; children: ReactNode; actions?: ReactNode }) => (
  <section className="card">
    {(title || actions) && <header className="card-h"><h3>{title}</h3><div>{actions}</div></header>}
    {children}
  </section>
);
export const ErrorBox = ({ message }: { message: string | null }) => (message ? <p role="alert" className="error">{message}</p> : null);
export const Loading = () => <p className="loading" role="status"><span className="loading-dot" aria-hidden="true" />Cargando…</p>;
export const Badge = ({ tone, children }: { tone: "ok" | "warn" | "info" | "muted"; children: ReactNode }) => <span className={`badge ${tone}`}>{children}</span>;
