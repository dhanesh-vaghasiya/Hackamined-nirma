import { createContext, useContext, useState, useEffect } from "react";
import toast from "react-hot-toast";
import api from "../services/api";

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On mount: validate session by calling /auth/me.
  // The httpOnly cookie is sent automatically — no token in JS.
  useEffect(() => {
    const verifySession = async () => {
      try {
        const { data } = await api.get("/auth/me");
        setUser(data.user);
        localStorage.setItem("user", JSON.stringify(data.user));
      } catch {
        // No valid cookie → user is not authenticated
        localStorage.removeItem("user");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    verifySession();
  }, []);

  const login = async (credentials) => {
    try {
      const { data } = await api.post("/auth/login", credentials);
      // Cookie is set automatically by the backend response
      localStorage.setItem("user", JSON.stringify(data.user));
      setUser(data.user);
      toast.success("Logged in successfully!");
      return data;
    } catch (error) {
      const msg = error.response?.data?.message || "Login failed";
      toast.error(msg);
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const { data } = await api.post("/auth/register", userData);
      // Cookie is set automatically by the backend response
      localStorage.setItem("user", JSON.stringify(data.user));
      setUser(data.user);
      toast.success("Account created successfully!");
      return data;
    } catch (error) {
      const msg = error.response?.data?.message || "Registration failed";
      toast.error(msg);
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Tell backend to clear the httpOnly cookie
      await api.post("/auth/logout");
    } catch {
      // Even if the call fails, clear local state
    }
    localStorage.removeItem("user");
    setUser(null);
    toast.success("Logged out successfully");
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
