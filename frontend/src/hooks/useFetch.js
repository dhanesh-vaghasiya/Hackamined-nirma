import { useCallback, useEffect, useState } from "react";
import { fetchWithFallback } from "../services/api";

export default function useFetch(endpoint, { refreshMs = 60000, config } = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isMock, setIsMock] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const result = await fetchWithFallback(endpoint, config);
    setData(result.data);
    setError(result.error || "");
    setIsMock(result.isMock);
    setLoading(false);
  }, [endpoint, config]);

  useEffect(() => {
    load();
    const timer = setInterval(load, refreshMs);
    return () => clearInterval(timer);
  }, [load, refreshMs]);

  return { data, loading, error, isMock, refetch: load };
}
