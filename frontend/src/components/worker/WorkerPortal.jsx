import { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle } from "lucide-react";

import WorkerInputForm from "./WorkerInputForm";
import { analyzeWorkerProfile } from "../../services/career";
import WorkerResultsUI, { EmptyState } from "./WorkerResultsUI";

const leftPanel = {
  idle: { flex: "1 1 55%", transition: { duration: 0.55, ease: [0.33, 1, 0.68, 1] } },
  analyzed: { flex: "1 1 38%", transition: { duration: 0.55, ease: [0.33, 1, 0.68, 1] } },
};

const WorkerPortal = ({ onProfileReady }) => {
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  const handleAnalyze = useCallback(async (payload) => {
    setError("");
    setIsLoading(true);
    try {
      const response = await analyzeWorkerProfile(payload);
      setProfile(response.profile || null);
      setAnalysis(response.analysis || null);
      setIsAnalyzed(true);
      if (response.profile?.id && onProfileReady) onProfileReady(response.profile.id);
    } catch (err) {
      const msg = err?.response?.data?.error || "Unable to analyze profile right now.";
      setError(msg);
      setIsAnalyzed(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div className="min-h-[calc(100vh-80px)] px-4 pb-6 pt-2">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-4">
        <h1 className="font-brand text-lg" style={{ color: "#dad7cd", fontWeight: 700 }}>Worker Intelligence Portal</h1>
        <p className="font-data text-xs" style={{ color: "#6B7265" }}>
          Assess individual vulnerability and generate personalized transition guidance.
        </p>
      </motion.div>

      {error && (
        <div className="mb-4 rounded-xl px-4 py-3 flex items-center gap-2" style={{ background: "rgba(220,38,38,0.08)", border: "1px solid rgba(220,38,38,0.25)" }}>
          <AlertTriangle size={16} style={{ color: "#DC2626" }} />
          <p className="font-data text-sm" style={{ color: "#dad7cd" }}>{error}</p>
        </div>
      )}

      <div className="flex gap-5 items-stretch" style={{ minHeight: "calc(100vh - 160px)" }}>
        <motion.div className="oasis-dash-card rounded-2xl p-5 overflow-hidden" variants={leftPanel} animate={isAnalyzed ? "analyzed" : "idle"} layout>
          <WorkerInputForm onAnalyze={handleAnalyze} isAnalyzed={isAnalyzed} isLoading={isLoading} />
        </motion.div>

        <motion.div className="flex-1 min-w-0" style={{ flex: isAnalyzed ? "1 1 62%" : "1 1 45%" }} layout>
          <AnimatePresence mode="wait">
            {isAnalyzed && analysis ? (
              <WorkerResultsUI key="results" analysis={analysis} profile={profile} profileId={profile?.id} />
            ) : (
              <div key="empty" className="oasis-dash-card rounded-2xl h-full">
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
