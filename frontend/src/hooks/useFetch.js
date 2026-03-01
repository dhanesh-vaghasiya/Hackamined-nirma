import { useState, useEffect, useCallback } from "react";
import api from "../services/api";

/**
 * Custom hook for API calls with loading/error state.
 * @param {string} url - API endpoint
 * @param {object} options - { method, immediate }
 */
const useFetch = (url, options = {}) => {
  const { method = "GET", immediate = true } = options;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(
    async (body = null) => {
      setLoading(true);
      setError(null);
      try {
        const config = { method, url };
        if (body) config.data = body;
        const response = await api(config);
        setData(response.data);
        return response.data;
      } catch (err) {
        setError(err.response?.data?.message || err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [url, method]
  );

  useEffect(() => {
    if (immediate && method === "GET") {
      execute();
    }
  }, [execute, immediate, method]);

  return { data, loading, error, execute };
};

export default useFetch;
