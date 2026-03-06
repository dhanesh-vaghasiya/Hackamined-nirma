import { motion } from "framer-motion";
import { BookOpen, CheckCircle2 } from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════
   DUMMY RESKILLING PATH
   ═══════════════════════════════════════════════════════════════════════ */

const STEPS = [
  {
    id: 1,
    week: "Wk 1–3",
    title: "NPTEL Data Basics",
    org: "IIT Madras",
    desc: "Foundations of data literacy, spreadsheet automation, and basic SQL queries.",
    active: true,
  },
  {
    id: 2,
    week: "Wk 4–5",
    title: "SWAYAM AI Fundamentals",
    org: "Govt. of India",
    desc: "Intro to machine learning concepts, prompt engineering, and AI-assisted workflows.",
    active: false,
  },
  {
    id: 3,
    week: "Wk 6–8",
    title: "PMKVY Digital Marketing",
    org: "Nagpur Center",
    desc: "Hands-on digital marketing certification — SEO, social media analytics, Google Ads basics.",
    active: false,
  },
  {
    id: 4,
    week: "Wk 9–10",
    title: "Capstone & Placement",
    org: "Oasis Network",
    desc: "Live project, portfolio build, and placement support through regional skill centres.",
    active: false,
  },
];

/* ═══════════════════════════════════════════════════════════════════════
   VARIANTS
   ═══════════════════════════════════════════════════════════════════════ */

const container = {
  initial: {},
  animate: { transition: { staggerChildren: 0.18, delayChildren: 0.3 } },
};

const stepVariant = {
  initial: { opacity: 0, x: -16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.4 } },
};

/* ═══════════════════════════════════════════════════════════════════════
   COMPONENT
   ═══════════════════════════════════════════════════════════════════════ */

const ReskillingStepper = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.25 }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <BookOpen size={15} style={{ color: "#97A87A" }} />
        <h3 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
          Reskilling Path
        </h3>
        <span
          className="ml-auto font-data text-[10px] px-2 py-0.5 rounded-full"
          style={{ color: "#97A87A", background: "rgba(151,168,122,0.12)" }}
        >
          10 Weeks
        </span>
      </div>

      {/* Timeline */}
      <motion.div
        variants={container}
        initial="initial"
        animate="animate"
        className="relative pl-6"
      >
        {/* Animated vertical line */}
        <motion.div
          className="absolute left-[9px] top-1 rounded-full"
          style={{ width: 2, background: "rgba(151,168,122,0.25)" }}
          initial={{ height: 0 }}
          animate={{ height: "100%" }}
          transition={{ duration: 1.2, delay: 0.35, ease: "easeOut" }}
        />

        {STEPS.map((step, i) => (
          <motion.div
            key={step.id}
            variants={stepVariant}
            className="relative pb-5 last:pb-0"
          >
            {/* Dot */}
            <div
              className="absolute -left-6 top-0.5 w-[18px] h-[18px] rounded-full flex items-center justify-center"
              style={{
                background: step.active ? "#97A87A" : "rgba(218,215,205,0.1)",
                border: `2px solid ${step.active ? "#97A87A" : "rgba(151,168,122,0.25)"}`,
                boxShadow: step.active ? "0 0 12px rgba(151,168,122,0.35)" : "none",
              }}
            >
              {step.active && <CheckCircle2 size={10} style={{ color: "#121412" }} />}
            </div>

            {/* Content */}
            <div
              className="rounded-lg px-3.5 py-3 transition-colors"
              style={{
                background: step.active
                  ? "rgba(151,168,122,0.08)"
                  : "rgba(218,215,205,0.03)",
                border: step.active
                  ? "1px solid rgba(151,168,122,0.2)"
                  : "1px solid transparent",
              }}
            >
              <div className="flex items-center gap-2 mb-1">
                <span
                  className="font-brand text-[11px] px-2 py-0.5 rounded"
                  style={{
                    fontWeight: 700,
                    color: step.active ? "#121412" : "#97A87A",
                    background: step.active ? "#97A87A" : "rgba(151,168,122,0.1)",
                  }}
                >
                  {step.week}
                </span>
                <span className="font-brand text-xs" style={{ color: "#dad7cd", fontWeight: 600 }}>
                  {step.title}
                </span>
              </div>
              <p className="font-data text-[11px]" style={{ color: "#97A87A", fontWeight: 500 }}>
                {step.org}
              </p>
              <p className="font-data text-xs mt-1 leading-relaxed" style={{ color: "#6B7265" }}>
                {step.desc}
              </p>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </motion.div>
  );
};

export default ReskillingStepper;
