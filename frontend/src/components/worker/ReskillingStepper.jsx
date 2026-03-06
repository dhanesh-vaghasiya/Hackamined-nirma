import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, CheckCircle2, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";

const container = {
  initial: {},
  animate: { transition: { staggerChildren: 0.18, delayChildren: 0.2 } },
};

const stepVariant = {
  initial: { opacity: 0, x: -16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.4 } },
};

const ReskillingStepper = ({ paths = [] }) => {
  const [expandedPath, setExpandedPath] = useState(0);

  if (!paths.length) {
    return (
      <div className="text-center py-6">
        <BookOpen size={20} style={{ color: "#6B7265", margin: "0 auto 8px" }} />
        <p className="font-data text-xs" style={{ color: "#6B7265" }}>No reskilling paths available yet.</p>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
      <div className="flex items-center gap-2 mb-4">
        <BookOpen size={15} style={{ color: "#97A87A" }} />
        <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
          Reskilling Paths
        </h3>
        <span className="ml-auto font-data text-[10px] px-2 py-0.5 rounded-full" style={{ color: "#97A87A", background: "rgba(151,168,122,0.12)" }}>
          {paths.length} Paths
        </span>
      </div>

      <div className="space-y-3">
        {paths.map((path, pathIdx) => (
          <div key={pathIdx} className="rounded-xl overflow-hidden" style={{ background: "rgba(218,215,205,0.03)", border: "1px solid rgba(151,168,122,0.12)" }}>
            {/* Path header */}
            <button
              onClick={() => setExpandedPath(expandedPath === pathIdx ? -1 : pathIdx)}
              className="w-full flex items-center gap-3 px-4 py-3 text-left cursor-pointer"
              style={{ background: expandedPath === pathIdx ? "rgba(151,168,122,0.06)" : "transparent" }}
            >
              <div className="flex-1 min-w-0">
                <p className="font-brand text-xs capitalize truncate" style={{ color: "#dad7cd", fontWeight: 600 }}>
                  {path.target_role?.replace(/_/g, " ")}
                </p>
                <p className="font-data text-[10px] mt-0.5" style={{ color: "#6B7265" }}>
                  {path.total_weeks} weeks · {path.hours_per_week}h/week · {path.hiring_count} jobs hiring
                </p>
              </div>
              <span className="font-data text-[10px] px-2 py-0.5 rounded-full shrink-0" style={{ color: path.target_role_vulnerability < 30 ? "#16A34A" : "#D97706", background: path.target_role_vulnerability < 30 ? "rgba(22,163,74,0.1)" : "rgba(217,119,6,0.1)" }}>
                Risk {path.target_role_vulnerability}/100
              </span>
              {expandedPath === pathIdx ? <ChevronUp size={14} style={{ color: "#6B7265" }} /> : <ChevronDown size={14} style={{ color: "#6B7265" }} />}
            </button>

            {/* Expanded steps */}
            <AnimatePresence>
              {expandedPath === pathIdx && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="overflow-hidden"
                >
                  <motion.div variants={container} initial="initial" animate="animate" className="relative pl-6 px-4 pb-4">
                    <motion.div className="absolute left-[25px] top-1 rounded-full" style={{ width: 2, background: "rgba(151,168,122,0.25)" }} initial={{ height: 0 }} animate={{ height: "100%" }} transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }} />

                    {(path.steps || []).map((step, idx) => (
                      <motion.div key={idx} variants={stepVariant} className="relative pb-4 last:pb-0">
                        <div className="absolute -left-6 top-0.5 w-[18px] h-[18px] rounded-full flex items-center justify-center" style={{ background: idx === 0 ? "#97A87A" : "rgba(218,215,205,0.1)", border: `2px solid ${idx === 0 ? "#97A87A" : "rgba(151,168,122,0.25)"}`, boxShadow: idx === 0 ? "0 0 12px rgba(151,168,122,0.35)" : "none" }}>
                          {idx === 0 && <CheckCircle2 size={10} style={{ color: "#121412" }} />}
                        </div>

                        <div className="rounded-lg px-3.5 py-3" style={{ background: idx === 0 ? "rgba(151,168,122,0.08)" : "rgba(218,215,205,0.03)", border: idx === 0 ? "1px solid rgba(151,168,122,0.2)" : "1px solid transparent" }}>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-brand text-[11px] px-2 py-0.5 rounded" style={{ fontWeight: 700, color: idx === 0 ? "#121412" : "#97A87A", background: idx === 0 ? "#97A87A" : "rgba(151,168,122,0.1)" }}>
                              Week {step.week_start}–{step.week_end}
                            </span>
                            <span className="font-brand text-xs truncate" style={{ color: "#dad7cd", fontWeight: 600 }}>{step.title}</span>
                          </div>
                          <p className="font-data text-[11px]" style={{ color: "#97A87A", fontWeight: 500 }}>
                            {step.provider}{step.institution ? ` · ${step.institution}` : ""} · {step.duration_weeks}w{step.is_free ? " · Free" : ""}
                          </p>
                          {step.skill_focus && (
                            <p className="font-data text-[10px] mt-1" style={{ color: "#6B7265" }}>Skills: {step.skill_focus}</p>
                          )}
                          {step.url && (
                            <a href={step.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 mt-1.5 font-data text-[10px] hover:underline" style={{ color: "#97A87A" }}>
                              <ExternalLink size={10} /> View Course
                            </a>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

export default ReskillingStepper;
