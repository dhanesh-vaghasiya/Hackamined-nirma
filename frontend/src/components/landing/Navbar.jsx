import { Link } from "react-router-dom";
import { motion } from "framer-motion";

const navLinks = [
  { to: "#", label: "Market Intelligence" },
  { to: "#", label: "Worker Portal" },
  { to: "#", label: "About" },
  { to: "/login", label: "Login" },
];

const Navbar = ({ user }) => {
  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="sticky top-0 z-30 py-5 backdrop-blur-sm"
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="relative h-9 w-9 rounded-full border border-[#9fe8705f] bg-[#9fe8701f]">
            <span className="absolute inset-0 m-auto h-2.5 w-2.5 rounded-full bg-[#d9ffb9] shadow-[0_0_14px_rgba(159,232,112,0.86)]" />
          </div>
          <div>
            <p className="font-brand text-[22px] font-bold leading-[0.9] tracking-tight text-white">OASIS</p>
            <p className="font-data text-[9px] uppercase tracking-[0.22em] text-[#97a298]">Workforce Intelligence</p>
          </div>
        </div>

        <nav className="hidden items-center gap-8 font-data text-[14px] text-[#b0bcb0] md:flex">
          {user ? (
            navLinks.map((item) => (
              <Link key={item.label} to={item.to} className="tracking-[0.02em] transition-colors hover:text-white">
                {item.label}
              </Link>
            ))
          ) : (
            <>
              {navLinks.map((item) => (
                <Link key={item.label} to={item.to} className="tracking-[0.02em] transition-colors hover:text-white">
                  {item.label}
                </Link>
              ))}
            </>
          )}
        </nav>
      </div>
    </motion.header>
  );
};

export default Navbar;
