import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./app/App";
import "./styles.css";
import "./pages/role-experience.css";
import "./pages/login-reference.css";
import "./pages/kawsay-welcome-responsive.css";
import "./pages/kawsay-encuadre-fix.css";
import "./pages/kawsay-design-reference.css";
import "./pages/kawsay-fidelity.css";
import "./pages/kawsay-login-visibility.css";
import "./pages/kawsay-layout-sin-recortes.css";
import "./pages/kawsay-brand.css";

class StartupBoundary extends React.Component<{ children: React.ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: unknown) { console.error("KAWSAY AI: fallo de interfaz", error); }
  render() {
    if (this.state.failed) {
      return <main style={{padding:"3rem",fontFamily:"system-ui",maxWidth:650,margin:"auto"}}>
        <h1>KAWSAY AI</h1>
        <p>No se pudo iniciar la interfaz. Prueba actualizar la página o abrirla en una ventana privada.</p>
        <button onClick={() => window.location.reload()}>Volver a intentar</button>
      </main>;
    }
    return this.props.children;
  }
}

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <React.StrictMode>
      <StartupBoundary>
        <BrowserRouter><App /></BrowserRouter>
      </StartupBoundary>
    </React.StrictMode>,
  );
}

// No permitir que un service worker antiguo bloquee la primera carga.
if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    void navigator.serviceWorker.register("/sw.js", { updateViaCache: "none" }).catch(error => {
      console.warn("KAWSAY AI: modo offline temporalmente no disponible", error);
    });
  });
}
