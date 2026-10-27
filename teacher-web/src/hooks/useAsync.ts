import { useCallback, useEffect, useRef, useState } from "react";
import { errMsg } from "../utils/format";

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const generation = useRef(0);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(() => {
    const current = ++generation.current;
    setLoading(true);
    return fn().then((d) => {
      if (current === generation.current) { setData(d); setError(null); }
    }).catch((e: unknown) => {
      if (current === generation.current) setError(errMsg(e));
    }).finally(() => {
      if (current === generation.current) setLoading(false);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { setData(null); void run(); return () => { generation.current++; }; }, [run]);
  return { data, error, loading, reload: run, setData };
}
