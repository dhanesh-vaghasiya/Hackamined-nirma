import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, Map, Globe, Play, Flag, GitBranch,
} from "lucide-react";
import SubConceptGraph from "./SubConceptGraph";

/* ── Topic card (left or right of spine) ───────────────────────── */
function TopicCard({ sec, idx, side, onClick }) {
  return (
    <div className="rm-topic-card">
      <button
        onClick={onClick}
        className="w-full flex items-center gap-2 rounded-lg px-3 py-2.5 cursor-pointer transition-all hover:shadow-[0_0_14px_rgba(151,168,122,0.12)]"
        style={{
          background: "rgba(218,215,205,0.05)",
          border: "1.5px solid rgba(151,168,122,0.12)",
          flexDirection: side === "left" ? "row-reverse" : "row",
        }}
      >
        <span
          className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 font-data text-[10px] font-bold"
          style={{
            background: "rgba(151,168,122,0.12)",
            color: "#97A87A",
            border: "1.5px solid rgba(151,168,122,0.25)",
          }}
        >
          {idx + 1}
        </span>
        <span
          className="font-brand text-[11px] flex-1"
          style={{
            color: "#dad7cd",
            fontWeight: 600,
            textAlign: side === "left" ? "right" : "left",
          }}
        >
          {sec.title}
        </span>
        <GitBranch size={11} className="shrink-0" style={{ color: "rgba(151,168,122,0.4)" }} />
      </button>
    </div>
  );
}

/* ── Main tree view ────────────────────────────────────────────── */
export default function RoadmapTreeView({ detailedRoadmap, onBack }) {
  const [graphTopic, setGraphTopic] = useState(null);

  if (!detailedRoadmap) return null;

  const sections = detailedRoadmap.sections || [];
  const roleName = detailedRoadmap.matched_from_role || detailedRoadmap.slug || "";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="oasis-dash-card rounded-2xl p-5"
    >
      {/* ── Header ── */}
      <div className="flex items-center gap-2 mb-1">
        <button
          onClick={onBack}
          className="p-1 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
        >
          <ArrowLeft size={16} style={{ color: "#97A87A" }} />
        </button>
        <Map size={15} style={{ color: "#97A87A" }} />
        <h3
          className="font-brand text-sm"
          style={{ color: "#dad7cd", fontWeight: 600 }}
        >
          {roleName}
        </h3>
      </div>
      <div className="flex items-center gap-3 ml-8 mb-6">
        <p className="font-data text-[10px]" style={{ color: "#6B7265" }}>
          {detailedRoadmap.total_topics} topics
        </p>
        {detailedRoadmap.source === "roadmap.sh" && (
          <span
            className="font-data text-[9px] px-1.5 py-0.5 rounded"
            style={{
              color: "#97A87A",
              background: "rgba(151,168,122,0.1)",
              border: "1px solid rgba(151,168,122,0.15)",
            }}
          >
            <Globe size={8} className="inline mr-1" style={{ marginBottom: 1 }} />
            roadmap.sh
          </span>
        )}
        <span className="font-data text-[9px]" style={{ color: "#6B7265" }}>
          Click a topic to explore its concept graph
        </span>
      </div>

      {/* ── Tree ── */}
      <div className="rm-tree">
        <div className="rm-spine" />

        {/* Start node */}
        <div className="flex justify-center mb-3 relative z-2">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center"
            style={{
              background: "#97A87A",
              boxShadow: "0 0 20px rgba(151,168,122,0.4)",
            }}
          >
            <Play size={14} style={{ color: "#121412" }} />
          </div>
        </div>

        {/* Topic rows */}
        {sections.map((sec, idx) => {
          const side = idx % 2 === 0 ? "left" : "right";
          return (
            <motion.div
              key={idx}
              className={`rm-row rm-row-${side}`}
              initial={{ opacity: 0, x: side === "left" ? -30 : 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05, duration: 0.4 }}
            >
              <div className="rm-col-left">
                {side === "left" && (
                  <TopicCard sec={sec} idx={idx} side={side} onClick={() => setGraphTopic(sec.title)} />
                )}
              </div>
              <div className="rm-col-center">
                <div className="rm-dot" style={{ background: "rgba(151,168,122,0.35)" }} />
              </div>
              <div className="rm-col-right">
                {side === "right" && (
                  <TopicCard sec={sec} idx={idx} side={side} onClick={() => setGraphTopic(sec.title)} />
                )}
              </div>
            </motion.div>
          );
        })}

        {/* End node */}
        <div className="flex justify-center mt-3 relative z-2">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center"
            style={{ background: "rgba(151,168,122,0.15)", border: "2px solid #97A87A" }}
          >
            <Flag size={10} style={{ color: "#97A87A" }} />
          </div>
        </div>
      </div>

      {/* Sub-concept graph overlay */}
      <AnimatePresence>
        {graphTopic && (
          <SubConceptGraph
            role={roleName}
            topic={graphTopic}
            onClose={() => setGraphTopic(null)}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}
