import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,   // Send httpOnly cookies with every request
  timeout: 60000,
});

// Auth endpoints that should NOT trigger a session wipe on 401
const AUTH_ENDPOINTS = ["/auth/login", "/auth/register", "/auth/me"];

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url || "";
    const isAuthEndpoint = AUTH_ENDPOINTS.some((ep) => requestUrl.includes(ep));

    // Only redirect for 401 on protected endpoints,
    // NOT on login/register/me (those handle 401 internally).
    if (error.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
