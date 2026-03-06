import { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Scan, Activity, AlertTriangle, Briefcase, MapPin, TrendingUp, TrendingDown,
  ChevronRight, Star, BookOpen, ExternalLink, ArrowLeft, Loader2, ShieldCheck, Zap, Bot,
} from "lucide-react";

import WorkerInputForm from "./WorkerInputForm";
import RiskScoreGauge from "./RiskScoreGauge";
import ReskillingStepper from "./ReskillingStepper";
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

function SuggestionCard({ role, match_score, reason, skills_to_learn, ai_risk_level, demand_outlook, rank, isSelected, onSelect }) {
  const scoreColor = match_score >= 0.7 ? "#97A87A" : match_score >= 0.4 ? "#D4A853" : "#DC2626";
  const riskColors = { LOW: "#16A34A", MEDIUM: "#D4A853", HIGH: "#DC2626", CRITICAL: "#DC2626" };
  const riskColor = riskColors[ai_risk_level] || "#D4A853";

  return (
    <motion.button
      onClick={onSelect}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0, transition: { delay: (rank - 1) * 0.08, duration: 0.35 } }}
      whileHover={{ scale: 1.01, borderColor: "rgba(151,168,122,0.35)" }}
      className="w-full text-left rounded-xl p-4 cursor-pointer transition-all"
      style={{
        background: isSelected ? "rgba(151,168,122,0.1)" : "rgba(151,168,122,0.04)",
        border: isSelected ? "1.5px solid rgba(151,168,122,0.4)" : "1px solid rgba(151,168,122,0.12)",
      }}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-data text-[10px] px-1.5 py-0.5 rounded font-bold" style={{ color: "#121412", background: "#97A87A" }}>#{rank}</span>
            <h4 className="font-brand text-sm truncate" style={{ color: "#dad7cd", fontWeight: 600 }}>{role}</h4>
          </div>
          <div className="flex items-center gap-3 mt-1.5">
            <div className="flex items-center gap-1">
              <ShieldCheck size={10} style={{ color: riskColor }} />
              <span className="font-data text-[10px]" style={{ color: riskColor }}>AI Risk: {ai_risk_level}</span>
            </div>
            {demand_outlook && (
              <div className="flex items-center gap-1">
                <TrendingUp size={10} style={{ color: "#6B7265" }} />
                <span className="font-data text-[10px]" style={{ color: "#6B7265" }}>{demand_outlook}</span>
              </div>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <div className="flex items-center gap-1">
            <Star size={11} style={{ color: scoreColor }} />
            <span className="font-data text-xs font-semibold" style={{ color: scoreColor }}>
              {Math.round(match_score * 100)}%
            </span>
          </div>
        </div>
      </div>

      {reason && (
        <p className="font-data text-[11px] leading-relaxed mb-2" style={{ color: "#8a8a7a" }}>{reason}</p>
      )}

      {skills_to_learn?.length > 0 && (
        <div>
          <span className="font-data text-[10px] font-semibold" style={{ color: "#6B7265" }}>Skills to learn:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {skills_to_learn.slice(0, 5).map((s, i) => (
              <span key={i} className="font-data text-[10px] px-1.5 py-0.5 rounded-full" style={{ color: "#D4A853", background: "rgba(212,168,83,0.08)", border: "1px solid rgba(212,168,83,0.18)" }}>{s}</span>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center gap-1 mt-3 pt-2" style={{ borderTop: "1px solid rgba(151,168,122,0.08)" }}>
        <span className="font-data text-[10px] font-semibold" style={{ color: "#97A87A" }}>
          {isSelected ? "Selected — Loading roadmap..." : "Click to get reskilling roadmap"}
        </span>
        <ChevronRight size={12} style={{ color: "#97A87A" }} />
      </div>
    </motion.button>
  );
}

function JobSuggestionsPanel({ suggestions, onSelectRole, selectedRole }) {
  if (!suggestions || !Array.isArray(suggestions) || suggestions.length === 0) return null;

  return (
    <motion.div variants={section} className="oasis-dash-card rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-1">
        <Briefcase size={15} style={{ color: "#97A87A" }} />
        <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>AI-Recommended Next Roles</h3>
      </div>
      <p className="font-data text-[10px] mb-4" style={{ color: "#6B7265" }}>
        Select a role to generate a personalized reskilling roadmap
      </p>

      <div className="space-y-2">
        {suggestions.map((rec, i) => (
          <SuggestionCard
            key={`${rec.role}-${i}`}
            {...rec}
            isSelected={selectedRole === rec.role}
            onSelect={() => onSelectRole(rec.role)}
          />
        ))}
      </div>

      <p className="font-data text-[9px] mt-3 text-right" style={{ color: "#4a4a42" }}>
        Powered by OASIS Deep Career Intelligence Engine
      </p>
    </motion.div>
  );
}

function RoadmapPanel({ roadmap, onBack }) {
  if (!roadmap) return null;

  return (
    <motion.div
      variants={section}
      initial="initial"
      animate="animate"
      className="oasis-dash-card rounded-2xl p-5"
    >
      <div className="flex items-center gap-2 mb-1">
        <button onClick={onBack} className="p-1 rounded-lg hover:bg-white/5 cursor-pointer transition-colors">
          <ArrowLeft size={16} style={{ color: "#97A87A" }} />
        </button>
        <BookOpen size={15} style={{ color: "#97A87A" }} />
        <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
          Reskilling Roadmap: {roadmap.target_role}
        </h3>
      </div>
      <p className="font-data text-[10px] ml-8 mb-4" style={{ color: "#6B7265" }}>
        {roadmap.total_weeks} weeks total plan
      </p>

      <div className="space-y-4 relative ml-3">
        {/* Timeline line */}
        <div className="absolute left-[7px] top-2 bottom-2 w-[2px] rounded-full" style={{ background: "rgba(151,168,122,0.2)" }} />

        {(roadmap.phases || []).map((phase, phaseIdx) => (
          <motion.div
            key={phaseIdx}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: phaseIdx * 0.12, duration: 0.4 }}
            className="relative pl-7"
          >
            {/* Timeline dot */}
            <div
              className="absolute left-0 top-1 w-4 h-4 rounded-full flex items-center justify-center z-10"
              style={{
                background: phaseIdx === 0 ? "#97A87A" : "rgba(218,215,205,0.1)",
                border: `2px solid ${phaseIdx === 0 ? "#97A87A" : "rgba(151,168,122,0.3)"}`,
                boxShadow: phaseIdx === 0 ? "0 0 12px rgba(151,168,122,0.35)" : "none",
              }}
            >
              <span className="font-data text-[8px] font-bold" style={{ color: phaseIdx === 0 ? "#121412" : "#97A87A" }}>{phase.phase || phaseIdx + 1}</span>
            </div>

            {/* Phase header */}
            <div className="flex items-center gap-2 mb-2">
              <span className="font-brand text-[11px] px-2 py-0.5 rounded" style={{ fontWeight: 700, color: phaseIdx === 0 ? "#121412" : "#97A87A", background: phaseIdx === 0 ? "#97A87A" : "rgba(151,168,122,0.1)" }}>
                Week {phase.week_start || "?"}–{phase.week_end || "?"}
              </span>
              <span className="font-brand text-xs" style={{ color: "#dad7cd", fontWeight: 600 }}>{phase.title}</span>
              {phase.hours_per_week && (
                <span className="font-data text-[9px] ml-auto" style={{ color: "#6B7265" }}>{phase.hours_per_week}h/week</span>
              )}
            </div>

            {/* Steps/Courses */}
            <div className="space-y-2">
              {(phase.steps || []).map((step, stepIdx) => (
                <div
                  key={stepIdx}
                  className="rounded-lg px-3.5 py-3"
                  style={{
                    background: "rgba(218,215,205,0.03)",
                    border: "1px solid rgba(151,168,122,0.1)",
                  }}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Zap size={10} style={{ color: "#D4A853" }} />
                    <span className="font-brand text-[11px]" style={{ color: "#dad7cd", fontWeight: 600 }}>{step.title}</span>
                  </div>
                  <p className="font-data text-[10px]" style={{ color: "#97A87A", fontWeight: 500 }}>
                    {step.provider}{step.duration_weeks ? ` · ${step.duration_weeks}w` : ""}{step.is_free ? " · Free" : ""}
                  </p>
                  {step.description && (
                    <p className="font-data text-[10px] mt-1" style={{ color: "#6B7265" }}>{step.description}</p>
                  )}
                  {step.skills_covered?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {step.skills_covered.map((s, si) => (
                        <span key={si} className="font-data text-[9px] px-1.5 py-0.5 rounded-full" style={{ color: "#97A87A", background: "rgba(151,168,122,0.08)", border: "1px solid rgba(151,168,122,0.15)" }}>{s}</span>
                      ))}
                    </div>
                  )}
                  {step.url && (
                    <a
                      href={step.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 mt-2 font-data text-[10px] hover:underline"
                      style={{ color: "#97A87A" }}
                    >
                      <ExternalLink size={10} /> Open Course
                    </a>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      {roadmap.expected_outcome && (
        <div className="mt-4 rounded-lg p-3" style={{ background: "rgba(151,168,122,0.06)", border: "1px solid rgba(151,168,122,0.15)" }}>
          <span className="font-data text-[10px] font-semibold" style={{ color: "#97A87A" }}>Expected Outcome</span>
          <p className="font-data text-[11px] mt-1 leading-relaxed" style={{ color: "#8a8a7a" }}>{roadmap.expected_outcome}</p>
        </div>
      )}

      {roadmap.certification_tip && (
        <p className="font-data text-[10px] mt-2" style={{ color: "#6B7265" }}>
          <strong style={{ color: "#D4A853" }}>Certification Tip:</strong> {roadmap.certification_tip}
        </p>
      )}
    </motion.div>
  );
}

function ResultsPanel({ analysis, profile, profileId }) {
  const skillDemandScore = analysis?.risk_score || 0;
  const paths = analysis?.reskilling_paths || [];
  const factors = analysis?.factors || [];
  const jobSuggestions = analysis?.job_suggestions || null;
  const aiVuln = analysis?.ai_vulnerability || {};

  const automationScore = aiVuln.automation_risk ?? 50;
  const takeoverScore = aiVuln.ai_takeover_risk ?? 50;
  const combinedAiScore = aiVuln.combined_ai_vulnerability ?? Math.round((automationScore + takeoverScore) / 2);

  const [selectedRole, setSelectedRole] = useState(null);
  const [roadmap, setRoadmap] = useState(null);
  const [roadmapLoading, setRoadmapLoading] = useState(false);
  const [roadmapError, setRoadmapError] = useState("");

  const handleSelectRole = async (role) => {
    if (selectedRole === role && roadmap) return;
    setSelectedRole(role);
    setRoadmap(null);
    setRoadmapError("");
    setRoadmapLoading(true);
    try {
      const res = await generateRoadmap(profileId, role);
      setRoadmap(res.roadmap || null);
    } catch (err) {
      setRoadmapError(err?.response?.data?.error || "Failed to generate roadmap.");
    } finally {
      setRoadmapLoading(false);
    }
  };

  const handleBackToRoles = () => {
    setSelectedRole(null);
    setRoadmap(null);
    setRoadmapError("");
  };

  return (
    <motion.div variants={rightFull} initial="initial" animate="animate" exit="exit" className="flex flex-col gap-4 h-full overflow-y-auto custom-scroll pr-1">

      {/* ── Dual Risk Cards ── */}
      <motion.div variants={section} className="grid grid-cols-2 gap-3">
        {/* Card 1: AI Automation Vulnerability (Groq-powered) */}
        <div className="oasis-dash-card rounded-2xl p-4">
          <div className="flex items-center gap-1.5 mb-2">
            <Bot size={14} style={{ color: "#D97706" }} />
            <h3 className="font-brand text-xs" style={{ color: "#dad7cd", fontWeight: 600 }}>AI Automation Risk</h3>
          </div>
          <RiskScoreGauge size={120} score={combinedAiScore} reason={aiVuln.automation_reason} />
          {/* <div className="mt-3 space-y-2">
            
            {aiVuln.ai_takeover_reason && (
              <p className="font-data text-[9px] leading-relaxed" style={{ color: "#6B7265" }}>{aiVuln.ai_takeover_reason}</p>
            )}
          </div> */}
        </div>

        {/* Card 2: Skill Demand Risk (DB/model-powered) */}
        <div className="oasis-dash-card rounded-2xl p-4">
          <div className="flex items-center gap-1.5 mb-2">
            <TrendingDown size={14} style={{ color: "#DC2626" }} />
            <h3 className="font-brand text-xs" style={{ color: "#dad7cd", fontWeight: 600 }}>Skill Demand Risk</h3>
          </div>
          <RiskScoreGauge size={120} score={skillDemandScore} riskLevel={analysis?.risk_level} />
          <div className="mt-3 space-y-2">
            <div className="flex items-center justify-between rounded-lg px-2.5 py-1.5" style={{ background: "rgba(151,168,122,0.08)", border: "1px solid rgba(151,168,122,0.18)" }}>
              <span className="font-data text-[10px]" style={{ color: "#8a8a7a" }}>Hiring Match</span>
              <span className="font-data text-[11px] font-bold" style={{ color: "#97A87A" }}> jobs ({analysis?.hiring_trend_pct ?? 0}%)</span>
            </div>
            {analysis?.growing_skills?.length > 0 && (
              <div className="rounded-lg px-2.5 py-1.5" style={{ background: "rgba(34,197,94,0.06)", border: "1px solid rgba(34,197,94,0.15)" }}>
                <span className="font-data text-[10px]" style={{ color: "#22C55E" }}>Growing: </span>
                <span className="font-data text-[10px]" style={{ color: "#97A87A" }}>{analysis.growing_skills.join(", ")}</span>
              </div>
            )}
            {analysis?.declining_skills?.length > 0 && (
              <div className="rounded-lg px-2.5 py-1.5" style={{ background: "rgba(220,38,38,0.06)", border: "1px solid rgba(220,38,38,0.12)" }}>
                <span className="font-data text-[10px]" style={{ color: "#DC2626" }}>Declining: </span>
                <span className="font-data text-[10px]" style={{ color: "#8a8a7a" }}>{analysis.declining_skills.join(", ")}</span>
              </div>
            )}
            {analysis?.factors?.length > 0 && (
              <p className="font-data text-[9px] leading-relaxed" style={{ color: "#6B7265" }}>
                {analysis.factors[analysis.factors.length - 1]}
              </p>
            )}
          </div>
        </div>
      </motion.div>

      {/* Show roadmap if a role is selected, otherwise show role suggestions */}
      <AnimatePresence mode="wait">
        {selectedRole && (roadmap || roadmapLoading || roadmapError) ? (
          <motion.div key="roadmap" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
            {roadmapLoading && (
              <motion.div className="oasis-dash-card rounded-2xl p-8 flex flex-col items-center justify-center gap-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}>
                  <Loader2 size={24} style={{ color: "#97A87A" }} />
                </motion.div>
                <p className="font-data text-xs" style={{ color: "#6B7265" }}>
                  Building personalized roadmap for <strong style={{ color: "#dad7cd" }}>{selectedRole}</strong>...
                </p>
              </motion.div>
            )}
            {roadmapError && (
              <div className="oasis-dash-card rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle size={14} style={{ color: "#DC2626" }} />
                  <span className="font-data text-xs" style={{ color: "#DC2626" }}>{roadmapError}</span>
                </div>
                <button onClick={handleBackToRoles} className="font-data text-[11px] cursor-pointer flex items-center gap-1 mt-1" style={{ color: "#97A87A" }}>
                  <ArrowLeft size={12} /> Back to role suggestions
                </button>
              </div>
            )}
            {roadmap && <RoadmapPanel roadmap={roadmap} onBack={handleBackToRoles} />}
          </motion.div>
        ) : (
          <motion.div key="suggestions" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
            <JobSuggestionsPanel
              suggestions={jobSuggestions}
              onSelectRole={handleSelectRole}
              selectedRole={selectedRole}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Only show old reskilling stepper if no Groq suggestions */}
      {!jobSuggestions && paths.length > 0 && (
        <motion.div variants={section} className="oasis-dash-card rounded-2xl p-5">
          <ReskillingStepper paths={paths} />
        </motion.div>
      )}

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
    </motion.div>
  );
}

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
              <ResultsPanel key="results" analysis={analysis} profile={profile} profileId={profile?.id} />
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
