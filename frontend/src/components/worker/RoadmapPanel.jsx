import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  Clock,
  ExternalLink,
  GraduationCap,
  Map,
  Sparkles,
  Target,
} from "lucide-react";

const card = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.45 } },
};

const stageExpand = {
  initial: { height: 0, opacity: 0 },
  animate: { height: "auto", opacity: 1, transition: { duration: 0.35, ease: [0.33, 1, 0.68, 1] } },
  exit: { height: 0, opacity: 0, transition: { duration: 0.25 } },
};

function StageBadge({ number, total }) {
  const pct = ((number / total) * 100).toFixed(0);
  return (
    <div
      className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
      style={{
        background: `conic-gradient(#97A87A ${pct}%, rgba(151,168,122,0.12) ${pct}%)`,
        color: "#dad7cd",
      }}
    >
      {number}
    </div>
  );
}

function CourseCard({ course }) {
  return (
    <a
      href={course.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-start gap-3 rounded-xl px-3 py-2.5 transition-colors"
      style={{
        background: "rgba(151,168,122,0.04)",
        border: "1px solid rgba(151,168,122,0.10)",
      }}
    >
      <GraduationCap size={14} style={{ color: "#97A87A", marginTop: 2 }} />
      <div className="min-w-0 flex-1">
        <p className="font-data text-xs font-medium truncate" style={{ color: "#dad7cd" }}>
          {course.title}
        </p>
        <p className="font-data text-[10px] mt-0.5" style={{ color: "#6B7265" }}>
          {course.institution}
          {course.duration ? ` · ${course.duration}` : ""}
        </p>
      </div>
      <ExternalLink size={12} style={{ color: "#6B7265", marginTop: 3 }} />
    </a>
  );
}

function StageItem({ stage, total }) {
  const [open, setOpen] = useState(false);
  const courses = stage.recommended_courses || [];
  const topics = stage.topics || [];

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ border: "1px solid rgba(151,168,122,0.12)", background: "rgba(26,28,25,0.6)" }}
    >
      <button
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-[rgba(151,168,122,0.04)]"
      >
        <StageBadge number={stage.stage_number} total={total} />
        <div className="flex-1 min-w-0">
          <p className="font-brand text-xs font-semibold truncate" style={{ color: "#dad7cd" }}>
            {stage.name}
          </p>
          {stage.duration && (
            <p className="font-data text-[10px] mt-0.5 flex items-center gap-1" style={{ color: "#6B7265" }}>
              <Clock size={10} /> {stage.duration}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {courses.length > 0 && (
            <span
              className="font-data text-[10px] px-1.5 py-0.5 rounded-full"
              style={{ color: "#97A87A", background: "rgba(151,168,122,0.10)" }}
            >
              {courses.length} course{courses.length > 1 ? "s" : ""}
            </span>
          )}
          {open ? (
            <ChevronDown size={14} style={{ color: "#6B7265" }} />
          ) : (
            <ChevronRight size={14} style={{ color: "#6B7265" }} />
          )}
        </div>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div variants={stageExpand} initial="initial" animate="animate" exit="exit" className="overflow-hidden">
            <div className="px-4 pb-4 space-y-3">
              {stage.description && (
                <p className="font-data text-xs leading-relaxed" style={{ color: "#6B7265" }}>
                  {stage.description}
                </p>
              )}

              {topics.length > 0 && (
                <div>
                  <p className="font-brand text-[10px] uppercase tracking-wider mb-1.5" style={{ color: "#97A87A" }}>
                    Topics
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {topics.map((t, i) => (
                      <span
                        key={i}
                        className="font-data text-[10px] px-2 py-0.5 rounded-full"
                        style={{ color: "#dad7cd", background: "rgba(151,168,122,0.08)", border: "1px solid rgba(151,168,122,0.12)" }}
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {stage.learning_outcomes?.length > 0 && (
                <div>
                  <p className="font-brand text-[10px] uppercase tracking-wider mb-1.5" style={{ color: "#97A87A" }}>
                    Outcomes
                  </p>
                  <ul className="space-y-1">
                    {stage.learning_outcomes.map((o, i) => (
                      <li key={i} className="font-data text-[10px] flex items-start gap-1.5" style={{ color: "#6B7265" }}>
                        <Target size={10} className="shrink-0 mt-0.5" style={{ color: "#97A87A" }} />
                        {o}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {courses.length > 0 && (
                <div>
                  <p className="font-brand text-[10px] uppercase tracking-wider mb-1.5" style={{ color: "#97A87A" }}>
                    NPTEL Courses
                  </p>
                  <div className="space-y-1.5">
                    {courses.map((c, i) => (
                      <CourseCard key={i} course={c} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function RoadmapPanel({ roadmapData }) {
  if (!roadmapData) return null;

  const final = roadmapData.final_roadmap || roadmapData;
  const stages = final.stages || [];
  const rec = roadmapData.recommended_skill || {};
  const skillName = typeof rec === "string" ? rec : rec.recommended_skill || final.skill || "Skill";
  const nptelAll = roadmapData.nptel_courses || [];

  return (
    <motion.div variants={card} initial="initial" animate="animate" className="flex flex-col gap-3">
      {/* Header */}
      <div className="oasis-dash-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-2">
          <Map size={15} style={{ color: "#97A87A" }} />
          <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
            {final.title || `Learning Roadmap: ${skillName}`}
          </h3>
        </div>
        {final.summary && (
          <p className="font-data text-xs leading-relaxed mb-2" style={{ color: "#6B7265" }}>
            {final.summary}
          </p>
        )}
        <div className="flex items-center gap-4 flex-wrap">
          {final.total_duration && (
            <span className="font-data text-[10px] flex items-center gap-1" style={{ color: "#97A87A" }}>
              <Clock size={10} /> {final.total_duration}
            </span>
          )}
          <span className="font-data text-[10px] flex items-center gap-1" style={{ color: "#97A87A" }}>
            <BookOpen size={10} /> {stages.length} stages
          </span>
          {nptelAll.length > 0 && (
            <span className="font-data text-[10px] flex items-center gap-1" style={{ color: "#97A87A" }}>
              <GraduationCap size={10} /> {nptelAll.length} courses
            </span>
          )}
        </div>

        {rec.reasoning && (
          <div
            className="mt-3 rounded-xl px-3 py-2.5"
            style={{ background: "rgba(151,168,122,0.05)", border: "1px solid rgba(151,168,122,0.10)" }}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <Sparkles size={10} style={{ color: "#97A87A" }} />
              <span className="font-brand text-[10px] uppercase tracking-wider" style={{ color: "#97A87A" }}>
                AI Recommendation
              </span>
            </div>
            <p className="font-data text-[10px] leading-relaxed" style={{ color: "#6B7265" }}>
              {rec.reasoning}
            </p>
          </div>
        )}
      </div>

      {/* Stages */}
      <div className="oasis-dash-card rounded-2xl p-5">
        <h4 className="font-brand text-xs mb-3" style={{ color: "#dad7cd", fontWeight: 600 }}>
          Learning Stages
        </h4>
        <div className="space-y-2">
          {stages.map((s, i) => (
            <StageItem key={i} stage={s} total={stages.length} />
          ))}
        </div>
      </div>

      {/* Career impact */}
      {final.career_impact && (
        <div className="oasis-dash-card rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={15} style={{ color: "#97A87A" }} />
            <h4 className="font-brand text-xs" style={{ color: "#dad7cd", fontWeight: 600 }}>Career Impact</h4>
          </div>
          <p className="font-data text-xs leading-relaxed" style={{ color: "#6B7265" }}>
            {final.career_impact}
          </p>
        </div>
      )}
    </motion.div>
  );
}
