import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Lightbulb, MapPin, Target } from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════
   STYLE CONSTANTS — Oasis theme
   ═══════════════════════════════════════════════════════════════════════ */

const cardBase = {
  background: "rgba(26,29,26,0.70)",
  backdropFilter: "blur(14px)",
  WebkitBackdropFilter: "blur(14px)",
  border: "1px solid rgba(151,168,122,0.25)",
  borderRadius: "12px",
};

const textPrimary = "#dad7cd";
const textMuted = "#6B7265";
const accentGreen = "#97A87A";

/* ═══════════════════════════════════════════════════════════════════════
   ANIMATION
   ═══════════════════════════════════════════════════════════════════════ */

const cardVariant = {
  initial: { opacity: 0, x: -18, scale: 0.97 },
  animate: {
    opacity: 1, x: 0, scale: 1,
    transition: { duration: 0.35, ease: "easeOut" },
  },
  exit: {
    opacity: 0, x: -12, scale: 0.97,
    transition: { duration: 0.2 },
  },
};

/* ═══════════════════════════════════════════════════════════════════════
   COMPACT INSIGHT CARD — one per question
   ═══════════════════════════════════════════════════════════════════════ */

function InsightCard({ deck, index, onClick }) {
  const skills = Array.isArray(deck.key_skills)
    ? deck.key_skills.slice(0, 3).join(", ")
    : (deck.key_skills || "").split(",").slice(0, 3).join(", ");

  return (
    <motion.div
      variants={cardVariant}
      style={cardBase}
      className="p-3 space-y-2 cursor-pointer transition-colors"
      onClick={onClick}
      whileHover={{
        borderColor: "rgba(151,168,122,0.50)",
        background: "rgba(26,29,26,0.85)",
      }}
    >
      {/* Topic + Goal row */}
      <div className="flex items-start gap-2">
        <Target size={12} style={{ color: accentGreen, marginTop: 2, flexShrink: 0 }} />
        <div className="min-w-0">
          <p className="text-[11px] font-semibold truncate" style={{ color: textPrimary }}>
            {deck.topic}
          </p>
          <p className="text-[10px] truncate" style={{ color: textMuted }}>
            Goal: {deck.goal}
          </p>
        </div>
      </div>

      {/* Key takeaway */}
      <div className="flex items-start gap-2">
        <Lightbulb size={12} style={{ color: accentGreen, marginTop: 2, flexShrink: 0 }} />
        <div className="min-w-0">
          <p className="text-[10px] leading-snug" style={{ color: textPrimary }}>
            {deck.focus_area}
          </p>
          {skills && (
            <p className="text-[9px] truncate mt-0.5" style={{ color: textMuted }}>
              {skills}
            </p>
          )}
        </div>
      </div>

      {/* Market snapshot */}
      <div className="flex items-start gap-2">
        <MapPin size={12} style={{ color: accentGreen, marginTop: 2, flexShrink: 0 }} />
        <p className="text-[10px] leading-snug" style={{ color: textMuted }}>
          {deck.market_regions && deck.market_regions !== "India-wide"
            ? `High demand: ${deck.market_regions}`
            : deck.market_demand}
        </p>
      </div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   MAIN COMPONENT — scrollable list of compact insight cards
   ═══════════════════════════════════════════════════════════════════════ */

const QuickInsightDeck = ({ decks = [], onInsightClick }) => {
  if (!decks || decks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full select-none px-4">
        <MessageSquare size={28} style={{ color: textMuted, opacity: 0.4 }} />
        <p className="text-[12px] text-center mt-3 max-w-[200px]" style={{ color: textMuted }}>
          Ask a question to generate your Quick Insight Deck
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 pt-4 pb-2 flex items-center justify-between">
        <h3
          className="font-brand text-xs font-bold tracking-wide uppercase"
          style={{ color: textPrimary }}
        >
          Quick Insight Deck
        </h3>
        <span className="text-[10px] font-mono" style={{ color: textMuted }}>
          {decks.length} {decks.length === 1 ? "insight" : "insights"}
        </span>
      </div>

      {/* Scrollable card list */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 custom-scroll space-y-2.5">
        <AnimatePresence initial={false}>
          {decks.map((deck, i) => (
            <InsightCard
              key={deck.id || `deck-${i}`}
              deck={deck}
              index={i}
              onClick={() => deck.messageId && onInsightClick?.(deck.messageId)}
            />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default QuickInsightDeck;
