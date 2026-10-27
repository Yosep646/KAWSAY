import { act, renderHook, waitFor } from "@testing-library/react";
import { expect, it } from "vitest";
import { useAsync } from "../hooks/useAsync";

it("una respuesta antigua no sobrescribe el aula recién seleccionada", async () => {
  let resolveOld!: (value: string) => void;
  const old = new Promise<string>((resolve) => { resolveOld = resolve; });
  const { result, rerender } = renderHook(({ room }) => useAsync(() => room === "old" ? old : Promise.resolve("Nueva aula"), [room]), { initialProps: { room: "old" } });
  rerender({ room: "new" });
  await waitFor(() => expect(result.current.data).toBe("Nueva aula"));
  await act(async () => { resolveOld("Antigua aula"); await old; });
  expect(result.current.data).toBe("Nueva aula");
  expect(result.current.loading).toBe(false);
});
