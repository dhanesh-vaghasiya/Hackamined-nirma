import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Scan, Activity } from "lucide-react";

import WorkerInputForm from "./WorkerInputForm";
import RiskScoreGauge from "./RiskScoreGauge";
import ReskillingStepper from "./ReskillingStepper";

/* ═══════════════════════════════════════════════════════════════════════
   ANIMATION VARIANTS
   ═══════════════════════════════════════════════════════════════════════ */

const leftPanel = {
  idle: { flex: "1 1 55%", transition: { duration: 0.55, ease: [0.33, 1, 0.68, 1] } },
  analyzed: { flex: "1 1 38%", transition: { duration: 0.55, ease: [0.33, 1, 0.68, 1] } },
};

const rightEmpty = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.5 } },
  exit: { opacity: 0, scale: 0.95, transition: { duration: 0.3 } },
};

const rightFull = {
  initial: { opacity: 0, x: 40 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.6, ease: [0.33, 1, 0.68, 1], staggerChildren: 0.15 } },
  exit: { opacity: 0, x: 40 },
};

const section = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.45 } },
};

/* ═══════════════════════════════════════════════════════════════════════
   EMPTY STATE
   ═══════════════════════════════════════════════════════════════════════ */

function EmptyState() {
  return (
    <motion.div
      variants={rightEmpty}
      initial="initial"
      animate="animate"
      exit="exit"
      className="h-full flex flex-col items-center justify-center text-center px-8"
    >
      {/* Glowing icon */}
      <motion.div
        className="w-20 h-20 rounded-full flex items-center justify-center mb-5"
        style={{
          background: "rgba(151,168,122,0.06)",
          border: "1px solid rgba(151,168,122,0.15)",
          boxShadow: "0 0 40px rgba(151,168,122,0.08)",
        }}
        animate={{
          boxShadow: [
            "0 0 40px rgba(151,168,122,0.08)",
            "0 0 60px rgba(151,168,122,0.18)",
            "0 0 40px rgba(151,168,122,0.08)",
          ],
        }}
        transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
      >
        <Scan size={28} style={{ color: "#97A87A", opacity: 0.7 }} />
      </motion.div>

      <h3 className="font-brand text-base mb-2" style={{ color: "#dad7cd", fontWeight: 600 }}>
        Awaiting Profile Data
      </h3>
      <p className="font-data text-xs max-w-[260px] leading-relaxed" style={{ color: "#6B7265" }}>
        Fill in the worker profile on the left and click <strong style={{ color: "#97A87A" }}>Analyze Profile</strong> to
        reveal a personalized risk score and reskilling roadmap.
      </p>

      {/* Subtle pulse dots */}
      <div className="flex gap-1.5 mt-6">
        {[0, 0.3, 0.6].map((delay) => (
          <motion.span
            key={delay}
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: "#97A87A" }}
            animate={{ opacity: [0.2, 0.8, 0.2] }}
            transition={{ repeat: Infinity, duration: 1.5, delay }}
          />
        ))}
      </div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   RESULTS PANEL
   ═══════════════════════════════════════════════════════════════════════ */

function ResultsPanel() {
  return (
    <motion.div
      variants={rightFull}
      initial="initial"
      animate="animate"
      exit="exit"
      className="flex flex-col gap-4 h-full overflow-y-auto custom-scroll pr-1"
    >
      {/* Risk Gauge */}
      <motion.div variants={section} className="oasis-dash-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Activity size={15} style={{ color: "#DC2626" }} />
          <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
            Vulnerability Score
          </h3>
        </div>
        <RiskScoreGauge score={74} />
      </motion.div>

      {/* Reskilling Stepper */}
      <motion.div variants={section} className="oasis-dash-card rounded-2xl p-5">
        <ReskillingStepper />
      </motion.div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   WORKER PORTAL (MAIN CONTAINER)
   ═══════════════════════════════════════════════════════════════════════ */

const WorkerPortal = () => {
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalyze = useCallback(() => {
    setIsLoading(true);
    // Simulate brief loading
    setTimeout(() => {
      setIsLoading(false);
      setIsAnalyzed(true);
    }, 1800);
  }, []);

  return (
    <div className="min-h-[calc(100vh-80px)] px-4 pb-6 pt-2">
      {/* Page header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-4"
      >
        <h1 className="font-brand text-lg" style={{ color: "#dad7cd", fontWeight: 700 }}>
          Worker Intelligence Portal
        </h1>
        <p className="font-data text-xs" style={{ color: "#6B7265" }}>
          Assess individual vulnerability and generate personalised reskilling roadmaps.
        </p>
      </motion.div>

      {/* Split-screen layout */}
      <div className="flex gap-5 items-stretch" style={{ minHeight: "calc(100vh - 160px)" }}>
        {/* ─── LEFT PANEL ─── */}
        <motion.div
          className="oasis-dash-card rounded-2xl p-5 overflow-hidden"
          variants={leftPanel}
          animate={isAnalyzed ? "analyzed" : "idle"}
          layout
        >
          <WorkerInputForm
            onAnalyze={handleAnalyze}
            isAnalyzed={isAnalyzed}
            isLoading={isLoading}
          />
        </motion.div>

        {/* ─── RIGHT PANEL ─── */}
        <motion.div
          className="flex-1 min-w-0"
          style={{ flex: isAnalyzed ? "1 1 62%" : "1 1 45%" }}
          layout
        >
          <AnimatePresence mode="wait">
            {isAnalyzed ? (
              <ResultsPanel key="results" />
            ) : (
              <div
                key="empty"
                className="oasis-dash-card rounded-2xl h-full"
              >
                <EmptyState />
              </div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
};

export default WorkerPortal;
