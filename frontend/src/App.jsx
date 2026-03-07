import { useState } from "react";
import { useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import AppRouter from "./routes/AppRouter";
import Navbar from "./components/Navbar";
import ParticleNetwork from "./components/three/ParticleNetwork";

/* page transition variants */
const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
};
const pageTransition = { duration: 0.35, ease: "easeInOut" };

/* routes where the Navbar should be visible */
const NAVBAR_ROUTES = ["/dashboard"];

function App() {
  const [activeLayer, setActiveLayer] = useState("Market Intelligence");
  const location = useLocation();
  const isLandingRoute = location.pathname === "/";

  const showNavbar = NAVBAR_ROUTES.some((r) =>
    location.pathname.startsWith(r)
  );

  return (
    <>
      {/* ── 3-D particle canvas (always behind everything) ── */}
      {!isLandingRoute && <ParticleNetwork />}

      {/* ── UI overlay ── */}
      <div className="relative" style={{ zIndex: 10 }}>
        {showNavbar && (
          <Navbar activeLayer={activeLayer} setActiveLayer={setActiveLayer} />
        )}

        <div style={{ paddingTop: showNavbar ? 64 : 0 }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname + activeLayer}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={pageTransition}
            >
              <AppRouter activeLayer={activeLayer} />
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </>
  );
}

export default App;
