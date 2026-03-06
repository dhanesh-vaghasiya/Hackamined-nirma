import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Eye, EyeOff, UserPlus } from "lucide-react";
import { motion } from "framer-motion";

const Register = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(form);
      navigate("/dashboard");
    } catch {
      /* handled */
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full px-4 py-2.5 rounded-lg text-sm font-data transition focus:outline-none focus:ring-2 placeholder:opacity-40";

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <motion.div
        className="w-full max-w-md"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        {/* Brand */}
        <div className="text-center mb-8">
          <div
            className="inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4"
            style={{ background: "rgba(151,168,122,0.2)", border: "1px solid rgba(151,168,122,0.4)" }}
          >
            <span className="font-brand" style={{ fontWeight: 800, fontSize: 20, color: "#97A87A" }}>O</span>
          </div>
          <h1 className="text-2xl font-brand" style={{ fontWeight: 700, color: "#FFFFFF" }}>
            Create your account
          </h1>
          <p className="font-data mt-1 text-sm" style={{ color: "#6B7265" }}>
            Get started with Oasis in seconds
          </p>
        </div>

        {/* Card */}
        <div className="glass-card-solid rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Name */}
            <div>
              <label className="block text-sm font-data mb-1.5" style={{ color: "#dad7cd", fontWeight: 500 }}>
                Full Name
              </label>
              <input
                type="text"
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="John Doe"
                required
                className={inputClass}
                style={{
                  background: "rgba(218,215,205,0.08)",
                  border: "1px solid rgba(151,168,122,0.2)",
                  color: "#FFFFFF",
                }}
                onFocus={(e) => (e.target.style.borderColor = "#97A87A")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(151,168,122,0.2)")}
              />
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-data mb-1.5" style={{ color: "#dad7cd", fontWeight: 500 }}>
                Email
              </label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="you@example.com"
                required
                className={inputClass}
                style={{
                  background: "rgba(218,215,205,0.08)",
                  border: "1px solid rgba(151,168,122,0.2)",
                  color: "#FFFFFF",
                }}
                onFocus={(e) => (e.target.style.borderColor = "#97A87A")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(151,168,122,0.2)")}
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-data mb-1.5" style={{ color: "#dad7cd", fontWeight: 500 }}>
                Password
              </label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  placeholder="Create a password"
                  required
                  minLength={6}
                  className={inputClass + " pr-10"}
                  style={{
                    background: "rgba(218,215,205,0.08)",
                    border: "1px solid rgba(151,168,122,0.2)",
                    color: "#FFFFFF",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "#97A87A")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(151,168,122,0.2)")}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer"
                  style={{ color: "#6B7265" }}
                >
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 font-brand text-sm py-2.5 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              style={{
                fontWeight: 600,
                background: "#97A87A",
                color: "#121412",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#A8B88D")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "#97A87A")}
            >
              {loading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <UserPlus size={18} />
                  Create Account
                </>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-sm font-data mt-6" style={{ color: "#6B7265" }}>
          Already have an account?{" "}
          <Link to="/login" style={{ color: "#97A87A", fontWeight: 600 }} className="hover:underline">
            Sign In
          </Link>
        </p>
      </motion.div>
    </div>
  );
};

export default Register;
