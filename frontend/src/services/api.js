import axios from "axios";
import { mockData } from "./mockData";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:5000",
  timeout: 12000,
});

export async function fetchWithFallback(endpoint, config = {}) {
  try {
    const response = await api.get(endpoint, config);
    return { data: response.data, isMock: false, error: null };
  } catch (error) {
    const mockResolver = mockData[endpoint];
    if (mockResolver) {
      return {
        data: typeof mockResolver === "function" ? mockResolver() : mockResolver,
        isMock: true,
        error: `Live API unavailable for ${endpoint}. Showing mock data.`,
      };
    }

    return {
      data: null,
      isMock: false,
      error: error?.response?.data?.message || "Data could not be loaded at the moment.",
    };
  }
}

export default api;
