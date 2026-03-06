import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Briefcase, MapPin, Clock, FileText, Sparkles, Loader2 } from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════
   CONSTANTS
   ═══════════════════════════════════════════════════════════════════════ */

const CITIES = [
  "Bengaluru", "Mumbai", "Pune", "Delhi NCR", "Hyderabad",
  "Chennai", "Indore", "Jaipur", "Nagpur", "Lucknow",
  "Bhopal", "Surat", "Coimbatore", "Kochi", "Chandigarh",
];

const MAX_WORDS = 200;

/* ═══════════════════════════════════════════════════════════════════════
   SHARED STYLES
   ═══════════════════════════════════════════════════════════════════════ */

const inputBase = {
  background: "rgba(218,215,205,0.07)",
  border: "1px solid rgba(151,168,122,0.2)",
  color: "#dad7cd",
  borderRadius: 10,
  outline: "none",
  transition: "border-color 0.25s, box-shadow 0.25s",
};

const focusRing = (e) => {
  e.target.style.borderColor = "#97A87A";
  e.target.style.boxShadow = "0 0 0 3px rgba(151,168,122,0.15)";
};
const blurRing = (e) => {
  e.target.style.borderColor = "rgba(151,168,122,0.2)";
  e.target.style.boxShadow = "none";
};

/* ═══════════════════════════════════════════════════════════════════════
   COMPONENT
   ═══════════════════════════════════════════════════════════════════════ */

const container = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const field = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

const WorkerInputForm = ({ onAnalyze, isAnalyzed, isLoading }) => {
  const [form, setForm] = useState({
    jobTitle: "",
    city: "",
    experience: "",
    tasks: "",
  });

  const wordCount = useMemo(() => {
    const trimmed = form.tasks.trim();
    return trimmed ? trimmed.split(/\s+/).length : 0;
  }, [form.tasks]);

  const canSubmit =
    form.jobTitle.trim() && form.city && form.experience && wordCount >= 5;

  const set = (key) => (e) => setForm((p) => ({ ...p, [key]: e.target.value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    if (canSubmit && !isLoading) onAnalyze(form);
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      variants={container}
      initial="initial"
      animate="animate"
      className="flex flex-col gap-4 h-full"
    >
      {/* Header */}
      <motion.div variants={field} className="mb-1">
        <h2 className="font-brand text-lg" style={{ color: "#dad7cd", fontWeight: 700 }}>
          Worker Profile
        </h2>
        <p className="font-data text-xs mt-1" style={{ color: "#6B7265" }}>
          Describe your current role and daily tasks — we'll map your vulnerability and reskilling path.
        </p>
      </motion.div>

      {/* Job Title */}
      <motion.div variants={field}>
        <Label icon={Briefcase} text="Job Title" />
        <input
          type="text"
          placeholder="e.g. Data Entry Operator"
          value={form.jobTitle}
          onChange={set("jobTitle")}
          disabled={isAnalyzed}
          className="w-full px-3.5 py-2.5 text-sm font-data placeholder:opacity-30"
          style={inputBase}
          onFocus={focusRing}
          onBlur={blurRing}
        />
      </motion.div>

      {/* City */}
      <motion.div variants={field}>
        <Label icon={MapPin} text="City" />
        <select
          value={form.city}
          onChange={set("city")}
          disabled={isAnalyzed}
          className="w-full px-3.5 py-2.5 text-sm font-data cursor-pointer appearance-none worker-select"
          style={{
            ...inputBase,
            color: form.city ? "#dad7cd" : "rgba(218,215,205,0.3)",
          }}
          onFocus={focusRing}
          onBlur={blurRing}
        >
          <option value="" disabled>Select city…</option>
          {CITIES.map((c) => (
            <option key={c} value={c} style={{ background: "#1A1D1A", color: "#dad7cd" }}>
              {c}
            </option>
          ))}
        </select>
      </motion.div>

      {/* Experience */}
      <motion.div variants={field}>
        <Label icon={Clock} text="Years of Experience" />
        <input
          type="number"
          min={0}
          max={50}
          placeholder="e.g. 4"
          value={form.experience}
          onChange={set("experience")}
          disabled={isAnalyzed}
          className="w-full px-3.5 py-2.5 text-sm font-data placeholder:opacity-30"
          style={inputBase}
          onFocus={focusRing}
          onBlur={blurRing}
        />
      </motion.div>

      {/* Tasks & Aspirations */}
      <motion.div variants={field} className="flex-1 flex flex-col">
        <Label icon={FileText} text="Daily Tasks & Aspirations" />
        <textarea
          placeholder="Describe what you do every day in your own words — include tools you use, repetitive tasks, and what you'd like to learn…"
          value={form.tasks}
          onChange={(e) => {
            const words = e.target.value.trim().split(/\s+/);
            if (e.target.value.trim() === "" || words.length <= MAX_WORDS) {
              setForm((p) => ({ ...p, tasks: e.target.value }));
            }
          }}
          disabled={isAnalyzed}
          rows={5}
          className="w-full px-3.5 py-2.5 text-sm font-data placeholder:opacity-30 resize-none flex-1 custom-scroll"
          style={{ ...inputBase, minHeight: 110 }}
          onFocus={focusRing}
          onBlur={blurRing}
        />
        {/* Word counter */}
        <div className="flex justify-end mt-1.5">
          <span
            className="font-data text-xs font-medium transition-colors duration-300"
            style={{
              color: wordCount >= 100 ? "#97A87A" : "#6B7265",
            }}
          >
            {wordCount} / {MAX_WORDS} words
          </span>
        </div>
      </motion.div>

      {/* Submit */}
      <motion.div variants={field}>
        <motion.button
          type="submit"
          disabled={!canSubmit || isLoading || isAnalyzed}
          className="w-full flex items-center justify-center gap-2 font-brand text-sm py-3 rounded-xl cursor-pointer transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            fontWeight: 700,
            background: isAnalyzed
              ? "rgba(151,168,122,0.15)"
              : "#97A87A",
            color: isAnalyzed ? "#97A87A" : "#121412",
            border: isAnalyzed
              ? "1px solid rgba(151,168,122,0.3)"
              : "1px solid transparent",
            boxShadow: isAnalyzed
              ? "none"
              : "0 0 20px rgba(151,168,122,0.2)",
          }}
          whileHover={
            !isAnalyzed && canSubmit
              ? { boxShadow: "0 0 32px rgba(151,168,122,0.35)", scale: 1.01 }
              : {}
          }
          whileTap={!isAnalyzed && canSubmit ? { scale: 0.98 } : {}}
        >
          {isLoading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : isAnalyzed ? (
            <>
              <Sparkles size={16} />
              Profile Analyzed
            </>
          ) : (
            <>
              <Sparkles size={16} />
              Analyze Profile
            </>
          )}
        </motion.button>
      </motion.div>
    </motion.form>
  );
};

/* ── tiny label helper ─────────────────────────────────────────────── */
function Label({ icon: Icon, text }) {
  return (
    <label className="flex items-center gap-1.5 mb-1.5">
      <Icon size={13} style={{ color: "#97A87A" }} />
      <span className="font-data text-xs" style={{ color: "#6B7265", fontWeight: 500 }}>
        {text}
      </span>
    </label>
  );
}

export default WorkerInputForm;
