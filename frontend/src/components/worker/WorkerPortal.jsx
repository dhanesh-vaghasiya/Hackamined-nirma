import { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Scan, Activity, AlertTriangle, Map, Loader2 } from "lucide-react";

import WorkerInputForm from "./WorkerInputForm";
import RiskScoreGauge from "./RiskScoreGauge";
import ReskillingStepper from "./ReskillingStepper";
import RoadmapPanel from "./RoadmapPanel";
import { analyzeWorkerProfile, generateRoadmap } from "../../services/career";

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

function EmptyState() {
  return (
    <motion.div variants={rightEmpty} initial="initial" animate="animate" exit="exit" className="h-full flex flex-col items-center justify-center text-center px-8">
      <motion.div className="w-20 h-20 rounded-full flex items-center justify-center mb-5" style={{ background: "rgba(151,168,122,0.06)", border: "1px solid rgba(151,168,122,0.15)", boxShadow: "0 0 40px rgba(151,168,122,0.08)" }} animate={{ boxShadow: ["0 0 40px rgba(151,168,122,0.08)", "0 0 60px rgba(151,168,122,0.18)", "0 0 40px rgba(151,168,122,0.08)"] }} transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}>
        <Scan size={28} style={{ color: "#97A87A", opacity: 0.7 }} />
      </motion.div>

      <h3 className="font-brand text-base mb-2" style={{ color: "#dad7cd", fontWeight: 600 }}>Awaiting Profile Data</h3>
      <p className="font-data text-xs max-w-[260px] leading-relaxed" style={{ color: "#6B7265" }}>
        Fill in the worker profile and click <strong style={{ color: "#97A87A" }}>Analyze Profile</strong> to reveal a personalized risk score and transition roadmap.
      </p>
    </motion.div>
  );
}

function ResultsPanel({ analysis, profile, roadmapData, onGenerateRoadmap, roadmapLoading }) {
  const score = analysis?.risk_score || 0;
  const paths = analysis?.reskilling_paths || [];
  const factors = analysis?.factors || [];

  return (
    <motion.div variants={rightFull} initial="initial" animate="animate" exit="exit" className="flex flex-col gap-4 h-full overflow-y-auto custom-scroll pr-1">
      <motion.div variants={section} className="oasis-dash-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Activity size={15} style={{ color: "#DC2626" }} />
          <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>Vulnerability Score</h3>
        </div>
        <RiskScoreGauge score={score} riskLevel={analysis?.risk_level} />
      </motion.div>

      <motion.div variants={section} className="oasis-dash-card rounded-2xl p-5">
        <ReskillingStepper paths={paths} />
      </motion.div>

      {factors.length > 0 && (
        <motion.div variants={section} className="oasis-dash-card rounded-2xl p-5">
          <h3 className="font-brand text-sm mb-2" style={{ color: "#dad7cd", fontWeight: 600 }}>Risk Factors</h3>
          <ul className="space-y-1.5">
            {factors.map((f, i) => (
              <li key={i} className="font-data text-xs flex items-start gap-2" style={{ color: "#6B7265" }}>
                <span style={{ color: "#DC2626", marginTop: 2 }}>•</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      )}

      <motion.div variants={section} className="oasis-dash-card rounded-2xl p-5">
        <h3 className="font-brand text-sm mb-2" style={{ color: "#dad7cd", fontWeight: 600 }}>Profile Snapshot</h3>
        <p className="font-data text-xs" style={{ color: "#6B7265" }}>
          {profile?.normalized_job_title || profile?.job_title} in {profile?.city} · {profile?.experience_years} years
        </p>
        {profile?.skills?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {profile.skills.slice(0, 8).map((s, i) => (
              <span key={i} className="font-data text-[10px] px-2 py-0.5 rounded-full" style={{ color: "#97A87A", background: "rgba(151,168,122,0.1)", border: "1px solid rgba(151,168,122,0.15)" }}>{s}</span>
            ))}
          </div>
        )}
      </motion.div>

      {/* Roadmap section */}
      <motion.div variants={section}>
        {!roadmapData && !roadmapLoading && (
          <button
            onClick={onGenerateRoadmap}
            className="w-full flex items-center justify-center gap-2 rounded-2xl px-5 py-3.5 font-brand text-sm font-semibold transition-all"
            style={{
              background: "linear-gradient(135deg, rgba(151,168,122,0.15) 0%, rgba(151,168,122,0.08) 100%)",
              border: "1px solid rgba(151,168,122,0.25)",
              color: "#97A87A",
            }}
          >
            <Map size={16} />
            Generate AI Learning Roadmap
          </button>
        )}

        {roadmapLoading && (
          <div
            className="w-full flex flex-col items-center justify-center gap-3 rounded-2xl px-5 py-8"
            style={{ background: "rgba(151,168,122,0.04)", border: "1px solid rgba(151,168,122,0.12)" }}
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}
            >
              <Loader2 size={24} style={{ color: "#97A87A" }} />
            </motion.div>
            <p className="font-data text-xs text-center" style={{ color: "#6B7265" }}>
              AI agent is analyzing market data, generating roadmap &amp; mapping NPTEL courses…
            </p>
            <p className="font-data text-[10px]" style={{ color: "#6B7265" }}>
              This may take up to a minute.
            </p>
          </div>
        )}

        {roadmapData && <RoadmapPanel roadmapData={roadmapData} />}
      </motion.div>
    </motion.div>
  );
}

const WorkerPortal = ({ onProfileReady }) => {
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [roadmapData, setRoadmapData] = useState(null);
  const [roadmapLoading, setRoadmapLoading] = useState(false);
  const [lastPayload, setLastPayload] = useState(null);

  const handleAnalyze = useCallback(async (payload) => {
    setError("");
    setIsLoading(true);
    setRoadmapData(null);
    setLastPayload(payload);
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

  const handleGenerateRoadmap = useCallback(async () => {
    if (!lastPayload) return;
    setRoadmapLoading(true);
    try {
      const roadmapPayload = {
        job_title: lastPayload.job_title,
        city: lastPayload.city,
        experience: lastPayload.experience,
        description: lastPayload.writeup || "",
        user_id: profile?.id,
      };
      const res = await generateRoadmap(roadmapPayload);
      if (res.success) {
        setRoadmapData(res.data);
      } else {
        setError(res.error || "Roadmap generation failed.");
      }
    } catch (err) {
      setError(err?.response?.data?.error || "Failed to generate roadmap.");
    } finally {
      setRoadmapLoading(false);
    }
  }, [lastPayload, profile]);

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
              <ResultsPanel
                key="results"
                analysis={analysis}
                profile={profile}
                roadmapData={roadmapData}
                onGenerateRoadmap={handleGenerateRoadmap}
                roadmapLoading={roadmapLoading}
              />
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
