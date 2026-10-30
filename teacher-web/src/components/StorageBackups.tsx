import { useState } from "react";
import { Icon } from "./Icon";
import { ErrorBox } from "./ui";
import { useAsync } from "../hooks/useAsync";
import { api, documentApi } from "../services/api";
import { errMsg } from "../utils/format";
import "./storage-backups.css";

interface StorageStatus {
  database: "ok" | "unavailable";
  engine: string;
  manual_backup_available: boolean;
  storage_persistence: "not_verified";
  render_environment: boolean;
  message: string;
}

/** Permite conservar una copia auténtica fuera del Render efímero. No promete
 * restauración automática ni persistencia de las bases del contenedor.
 */
export function StorageBackups() {
  const status = useAsync(() => api.get<StorageStatus>("/admin/storage/status"), []);
  const [exporting, setExporting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  async function exportBackup() {
    if (exporting || !status.data?.manual_backup_available) return;
    if (!window.confirm(
      "Este respaldo contiene información sensible de KAWSAY AI, incluidos datos escolares. " +
      "Descárgalo únicamente en tu equipo de confianza y guárdalo en una unidad cifrada. " +
      "¿Deseas continuar?"
    )) return;

    setExporting(true);
    setProblem(null);
    setFeedback(null);
    try {
      const blob = await documentApi.download("/admin/storage/export");
      if (!blob.size) throw new Error("El servidor devolvió un archivo vacío.");
      const objectUrl = URL.createObjectURL(blob);
      try {
        const link = document.createElement("a");
        link.href = objectUrl;
        link.download = `kawsay-respaldo-${new Date().toISOString().replace(/[:.]/g, "-")}.db`;
        document.body.appendChild(link);
        link.click();
        link.remove();
      } finally {
        // No revocar inmediatamente: navegadores móviles necesitan tiempo para iniciar la descarga.
        window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
      }
      setFeedback("Se solicitó la descarga. Comprueba que el archivo .db se haya guardado antes de cerrar esta página.");
    } catch (error) {
      setProblem(errMsg(error));
    } finally {
      setExporting(false);
    }
  }

  return <section className="admin-supplement storage-backups" aria-label="Respaldos de base de datos">
    <header className="storage-backups-header">
      <span className="storage-backups-mark"><Icon name="database" /></span>
      <div>
        <h2>Respaldo de información</h2>
        <p>Consulta la conexión a SQLite y descarga una copia íntegra de los registros.</p>
      </div>
    </header>

    <div className="storage-backups-stats" aria-label="Estado real del almacenamiento">
      <div><span>Base de datos</span><strong>{status.loading ? "Verificando…" : status.data?.database === "ok" ? "SQLite conectada" : "No verificada"}</strong></div>
      <div><span>Exportación manual</span><strong>{status.data?.manual_backup_available ? "Disponible" : status.loading ? "Verificando…" : "No disponible"}</strong></div>
      <div><span>Persistencia tras reinicios</span><strong>Sin garantía verificada</strong></div>
    </div>

    <ErrorBox message={status.error ? `No se pudo comprobar la base de datos: ${status.error}` : null} />
    <ErrorBox message={problem} />
    {feedback && <p role="status" className="notice">{feedback}</p>}

    <div className="storage-backups-action">
      <div>
        <h3>Descargar copia de seguridad</h3>
        <p>Genera una copia consistente de la base, incluyendo las transacciones guardadas. El archivo se descarga en tu equipo y no queda protegido automáticamente por Render.</p>
      </div>
      <button type="button" className="storage-backups-download"
        onClick={() => { void exportBackup(); }}
        disabled={!status.data?.manual_backup_available || exporting}
        aria-busy={exporting}>
        <Icon name="database" /> {exporting ? "Preparando copia…" : "Descargar respaldo .db"}
      </button>
    </div>

    <p className="storage-backups-note"><Icon name="shield" />
      {status.data?.render_environment
        ? "Esta instalación se ejecuta en Render. El respaldo manual ayuda a evitar pérdidas, pero no impide que el almacenamiento temporal se borre al reiniciar o desplegar."
        : "No hay una confirmación de durabilidad del disco. Conserva copias en un lugar externo seguro antes de reinicios o migraciones."}
    </p>
    <button type="button" className="ghost" onClick={() => void status.reload()}
      disabled={status.loading}> <Icon name="refresh" /> Actualizar estado </button>
    <p className="storage-backups-privacy">Los respaldos pueden contener información personal de estudiantes. No los compartas por enlaces públicos ni los subas a GitHub. Este panel no restaura copias automáticamente.</p>
  </section>;
}
