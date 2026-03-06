import { useState, useEffect, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Loader2, GitBranch } from "lucide-react";
import { fetchTopicGraph } from "../../services/career";

/* ── Bubble colors — OASIS-themed translucent tones ────────────── */
const BUBBLE_COLORS = [
  { bg: "rgba(151,168,122,0.22)", border: "rgba(151,168,122,0.45)", text: "#dad7cd" },  // sage
  { bg: "rgba(212,168,83,0.18)",  border: "rgba(212,168,83,0.40)",  text: "#dad7cd" },  // gold
  { bg: "rgba(107,114,101,0.25)", border: "rgba(107,114,101,0.45)", text: "#dad7cd" },  // moss
  { bg: "rgba(168,192,142,0.20)", border: "rgba(168,192,142,0.42)", text: "#dad7cd" },  // mint
  { bg: "rgba(218,215,205,0.12)", border: "rgba(218,215,205,0.28)", text: "#dad7cd" },  // sand
  { bg: "rgba(140,160,120,0.20)", border: "rgba(140,160,120,0.40)", text: "#dad7cd" },  // olive
];

/* ── Radial bubble layout ─────────────────────────────────────────
   Places root in center, other nodes in a circle around it.       */

const BUBBLE_RX = 68;
const BUBBLE_RY = 28;

function computeBubblePositions(nodes, rootId) {
  const positions = {};
  const CX = 280;
  const CY = 200;
  const RADIUS = 150;

  const root = nodes.find((n) => n.id === rootId) || nodes[0];
  const others = nodes.filter((n) => n.id !== root.id);

  positions[root.id] = { x: CX, y: CY };

  others.forEach((n, i) => {
    const angle = ((2 * Math.PI) / others.length) * i - Math.PI / 2;
    positions[n.id] = {
      x: CX + RADIUS * Math.cos(angle),
      y: CY + RADIUS * Math.sin(angle),
    };
  });

  return { positions, width: CX * 2, height: CY * 2 };
}

/* ── Curved edge between two bubble centers ────────────────────── */
function BubbleEdge({ from, to, positions, idx }) {
  const pFrom = positions[from];
  const pTo = positions[to];
  if (!pFrom || !pTo) return null;

  const dx = pTo.x - pFrom.x;
  const dy = pTo.y - pFrom.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist === 0) return null;

  // Shorten line so it stops at ellipse boundary
  const shrinkFrom = BUBBLE_RX * 0.7;
  const shrinkTo = BUBBLE_RX * 0.7;
  const ux = dx / dist;
  const uy = dy / dist;
  const x1 = pFrom.x + ux * shrinkFrom;
  const y1 = pFrom.y + uy * shrinkFrom;
  const x2 = pTo.x - ux * shrinkTo;
  const y2 = pTo.y - uy * shrinkTo;

  // Slight curve via perpendicular offset
  const perpX = -uy * 20;
  const perpY = ux * 20;
  const cx = (x1 + x2) / 2 + perpX;
  const cy = (y1 + y2) / 2 + perpY;

  const d = `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`;

  return (
    <motion.path
      d={d}
      fill="none"
      stroke="rgba(180,190,170,0.4)"
      strokeWidth={2.5}
      initial={{ pathLength: 0, opacity: 0 }}
      animate={{ pathLength: 1, opacity: 1 }}
      transition={{ delay: 0.2 + idx * 0.06, duration: 0.5 }}
    />
  );
}

/* ── Bubble Node ───────────────────────────────────────────────── */
function BubbleNode({ node, pos, isRoot, colorIdx, idx }) {
  const [showDesc, setShowDesc] = useState(false);
  const c = BUBBLE_COLORS[colorIdx % BUBBLE_COLORS.length];

  const rx = isRoot ? BUBBLE_RX + 10 : BUBBLE_RX;
  const ry = isRoot ? BUBBLE_RY + 6 : BUBBLE_RY;

  return (
    <motion.g
      initial={{ opacity: 0, scale: 0.3 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.1 + idx * 0.08, duration: 0.4, type: "spring", stiffness: 200 }}
      style={{ cursor: "pointer" }}
      onClick={() => setShowDesc(!showDesc)}
    >
      {/* Glow */}
      <ellipse cx={pos.x} cy={pos.y} rx={rx + 4} ry={ry + 4} fill="none" stroke={c.border} strokeWidth={1} opacity={0.25} />
      {/* Shadow */}
      <ellipse cx={pos.x + 2} cy={pos.y + 3} rx={rx} ry={ry} fill="rgba(0,0,0,0.2)" />
      {/* Bubble */}
      <ellipse
        cx={pos.x}
        cy={pos.y}
        rx={rx}
        ry={ry}
        fill={c.bg}
        stroke={c.border}
        strokeWidth={2}
      />
      {/* Label */}
      <foreignObject x={pos.x - rx + 6} y={pos.y - ry + 4} width={(rx - 6) * 2} height={(ry - 4) * 2}>
        <div
          className="flex items-center justify-center h-full"
          style={{ pointerEvents: "none" }}
        >
          <span
            className="font-brand leading-tight text-center"
            style={{
              color: c.text,
              fontSize: isRoot ? 11 : 10,
              fontWeight: 700,
              textShadow: "0 1px 3px rgba(0,0,0,0.3)",
            }}
          >
            {node.label}
          </span>
        </div>
      </foreignObject>

      {/* Description tooltip */}
      {showDesc && node.description && (
        <foreignObject x={pos.x - 80} y={pos.y + ry + 6} width={160} height={50}>
          <div
            className="rounded-lg px-2 py-1.5"
            style={{
              background: "rgba(26,30,26,0.95)",
              border: "1px solid rgba(151,168,122,0.2)",
              backdropFilter: "blur(8px)",
            }}
          >
            <p className="font-data text-center leading-snug" style={{ color: "#dad7cd", fontSize: 9 }}>
              {node.description}
            </p>
          </div>
        </foreignObject>
      )}
    </motion.g>
  );
}

/* ── Main SubConceptGraph ────────────────────────────────────────── */
export default function SubConceptGraph({ role, topic, onClose }) {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadGraph = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetchTopicGraph(role, topic);
      setGraphData(res.graph);
    } catch (err) {
      setError(err?.response?.data?.error || "Failed to load concept graph");
    } finally {
      setLoading(false);
    }
  }, [role, topic]);

  useEffect(() => { loadGraph(); }, [loadGraph]);

  const layout = useMemo(() => {
    if (!graphData) return null;
    return computeBubblePositions(graphData.nodes, graphData.root);
  }, [graphData]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="sc-overlay"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <motion.div
        className="sc-panel oasis-dash-card"
        initial={{ y: 30, scale: 0.95 }}
        animate={{ y: 0, scale: 1 }}
        exit={{ y: 30, scale: 0.95 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-3 px-1">
          <div className="flex items-center gap-2">
            <GitBranch size={14} style={{ color: "#97A87A" }} />
            <h4 className="font-brand text-xs" style={{ color: "#dad7cd", fontWeight: 600 }}>
              {topic}
            </h4>
            <span className="font-data text-[9px] px-1.5 py-0.5 rounded" style={{ color: "#6B7265", background: "rgba(218,215,205,0.06)", border: "1px solid rgba(151,168,122,0.1)" }}>
              Concept Graph
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
          >
            <X size={14} style={{ color: "#6B7265" }} />
          </button>
        </div>

        <p className="font-data text-[9px] mb-2 px-1" style={{ color: "#6B7265" }}>
          Click any bubble to see a description. Lines show how concepts connect.
        </p>

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-14 gap-3">
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}>
              <Loader2 size={22} style={{ color: "#97A87A" }} />
            </motion.div>
            <p className="font-data text-[10px]" style={{ color: "#6B7265" }}>
              Building concept graph for <strong style={{ color: "#dad7cd" }}>{topic}</strong>...
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="text-center py-10">
            <p className="font-data text-[11px]" style={{ color: "#DC2626" }}>{error}</p>
            <button onClick={loadGraph} className="font-data text-[10px] mt-2 cursor-pointer" style={{ color: "#97A87A" }}>
              Retry
            </button>
          </div>
        )}

        {/* Graph */}
        {!loading && !error && graphData && layout && (
          <div className="sc-canvas-wrap custom-scroll">
            <svg
              width={layout.width}
              height={layout.height}
              viewBox={`0 0 ${layout.width} ${layout.height}`}
              className="sc-canvas"
            >
              {/* Edges first (behind bubbles) */}
              {graphData.edges.map((e, i) => (
                <BubbleEdge
                  key={`${e.from}-${e.to}`}
                  from={e.from}
                  to={e.to}
                  positions={layout.positions}
                  idx={i}
                />
              ))}

              {/* Bubble nodes */}
              {graphData.nodes.map((n, i) => (
                <BubbleNode
                  key={n.id}
                  node={n}
                  pos={layout.positions[n.id] || { x: 280, y: 200 }}
                  isRoot={n.id === graphData.root}
                  colorIdx={i}
                  idx={i}
                />
              ))}
            </svg>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
