import { Routes, Route, Navigate } from "react-router-dom";
import Landing from "../pages/Landing";
import Login from "../pages/Login";
import Register from "../pages/Register";
import Dashboard from "../pages/Dashboard";
import ProtectedRoute from "./ProtectedRoute";
import GuestRoute from "./GuestRoute";

const AppRouter = ({ activeLayer }) => {
  return (
    <Routes>
      {/* Public route */}
      <Route path="/" element={<Landing />} />

      {/* Guest-only: redirect to dashboard if already logged in */}
      <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
      <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />

      {/* Protected: only logged-in users */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard activeLayer={activeLayer} />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default AppRouter;
