import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * GuestRoute — only accessible to unauthenticated users.
 * If the user is already logged in, redirect them to /dashboard.
 */
const GuestRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#121412" }}>
        <div className="flex flex-col items-center gap-3">
          <span className="w-8 h-8 border-2 rounded-full animate-spin" style={{ borderColor: "rgba(151,168,122,0.2)", borderTopColor: "#97A87A" }} />
          <p className="font-data text-sm" style={{ color: "#6B7265" }}>Loading…</p>
        </div>
      </div>
    );
  }

  if (user) return <Navigate to="/dashboard" replace />;

  return children;
};

export default GuestRoute;
