import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StorageBackups } from "../components/StorageBackups";
import { api, documentApi } from "../services/api";

afterEach(() => vi.restoreAllMocks());

const available = {
  database: "ok",
  engine: "SQLite",
  manual_backup_available: true,
  storage_persistence: "not_verified",
  render_environment: true,
  message: "SQLite está accesible, sin garantía de durabilidad.",
};

describe("Respaldos administrativos de KAWSAY", () => {
  it("presenta el estado que devolvió el backend sin inventar persistencia", async () => {
    vi.spyOn(api, "get").mockResolvedValue(available);
    render(<StorageBackups />);
    expect(await screen.findByText("SQLite conectada")).toBeInTheDocument();
    expect(screen.getByText("Sin garantía verificada")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Descargar respaldo/ })).toBeEnabled();
    expect(screen.getByText(/Render.*almacenamiento temporal/)).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith("/admin/storage/status");
  });

  it("impide descargar si SQLite no está disponible", async () => {
    vi.spyOn(api, "get").mockResolvedValue({
      ...available, database: "unavailable", manual_backup_available: false,
    });
    render(<StorageBackups />);
    await screen.findByText("No verificada");
    expect(screen.getByRole("button", { name: /Descargar respaldo/ })).toBeDisabled();
  });

  it("requiere confirmación antes de descargar información sensible", async () => {
    vi.spyOn(api, "get").mockResolvedValue(available);
    const download = vi.spyOn(documentApi, "download");
    vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<StorageBackups />);
    await screen.findByText("SQLite conectada");
    await userEvent.click(screen.getByRole("button", { name: /Descargar respaldo/ }));
    await waitFor(() => expect(window.confirm).toHaveBeenCalled());
    expect(download).not.toHaveBeenCalled();
  });
});
