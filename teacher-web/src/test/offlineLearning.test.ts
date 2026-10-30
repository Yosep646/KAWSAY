import { beforeEach, expect, it, vi } from "vitest";
import { api } from "../services/api";
import { synchronizeOffline } from "../services/offlineLearning";
import { offlineVault, type VaultData } from "../services/offlineVault";

vi.mock("../services/offlineVault", () => ({ offlineVault: { isOpen: vi.fn(), snapshot: vi.fn(), update: vi.fn() } }));
let data: VaultData;
beforeEach(() => {
  vi.restoreAllMocks();
  data = { user: { id: "student", role: "STUDENT", display_name: "Ficticio" }, deviceId: "device", verifiedAt: 1,
    tasks: [], statuses: {}, pending: ["one", "two"].map(eventId => ({ key: "student:task", deviceId: "device",
      event: { event_id: eventId, type: "attempt.created", payload: { student_assignment_id: "task" } } })) };
  vi.mocked(offlineVault.isOpen).mockReturnValue(true);
  vi.mocked(offlineVault.snapshot).mockImplementation(async () => structuredClone(data));
  vi.mocked(offlineVault.update).mockImplementation(async change => { change(data); return data; });
  vi.spyOn(api, "get").mockImplementation(async path => path === "/auth/me" ? { id: "student", role: "STUDENT" } : { questions: [] });
});

const invalidAcknowledgements = [
  [],
  [{ event_id: "one", status: "ACKED" }, { event_id: "one", status: "ACKED" }],
  [{ event_id: "one", status: "ACKED" }, { event_id: "other", status: "ACKED" }],
  [{ event_id: "one", status: "ACKED" }, { event_id: "two", status: "UNKNOWN" }],
].map(results => ({ results }));
it.each(invalidAcknowledgements)("conserva toda la cola ante una confirmación incompleta, duplicada o ajena: $results", async ({ results }) => {
  vi.spyOn(api, "post").mockResolvedValue({ results });
  await expect(synchronizeOffline("student")).rejects.toThrow("Confirmación inválida");
  expect(data.pending).toHaveLength(2);
  expect(offlineVault.update).not.toHaveBeenCalled();
});

it("confirma individualmente ACKED/DUPLICATE y conserva un rechazo para revisión", async () => {
  vi.spyOn(api, "post").mockResolvedValue({ results: [{ event_id: "one", status: "DUPLICATE" }, { event_id: "two", status: "REJECTED" }] });
  await expect(synchronizeOffline("student")).rejects.toThrow("revisión docente");
  expect(data.pending.map(p => p.event.event_id)).toEqual(["two"]);
});

it("conserva los eventos si la conexión se interrumpe después del ACK pero antes del estado oficial", async () => {
  vi.spyOn(api, "post").mockResolvedValue({ results: [{ event_id: "one", status: "ACKED" }, { event_id: "two", status: "ACKED" }] });
  vi.mocked(api.get).mockResolvedValueOnce({ id: "student", role: "STUDENT" }).mockRejectedValueOnce(new Error("red interrumpida"));
  await expect(synchronizeOffline("student")).rejects.toThrow("red interrumpida");
  expect(data.pending).toHaveLength(2);
});

it("verifica identidad remota y no envía respuestas con la sesión de otra cuenta", async () => {
  vi.mocked(api.get).mockResolvedValue({ id: "other-student", role: "STUDENT" });
  const post = vi.spyOn(api, "post");
  await expect(synchronizeOffline("student")).rejects.toThrow("cuenta que descargó");
  expect(post).not.toHaveBeenCalled();
  expect(data.pending).toHaveLength(2);
});

it("no borra una respuesta nueva guardada mientras el servidor confirma otras", async () => {
  vi.spyOn(api, "post").mockImplementation(async () => {
    data.pending.push({ key: "student:task", deviceId: "device", event: { event_id: "new", type: "attempt.created", payload: {} } });
    return { results: [{ event_id: "one", status: "ACKED" }, { event_id: "two", status: "ACKED" }] };
  });
  expect(await synchronizeOffline("student")).toBe(2);
  expect(data.pending.map(p => p.event.event_id)).toEqual(["new"]);
});
