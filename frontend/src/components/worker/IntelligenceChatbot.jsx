import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Sparkles, Loader2 } from "lucide-react";
import { sendChatMessage } from "../../services/chatbot";

/* ═══════════════════════════════════════════════════════════════════════
   SUGGESTION PILLS – 5 required question types from PPT
   ═══════════════════════════════════════════════════════════════════════ */

const SUGGESTIONS = [
  "Why is my risk score so high?",
  "What jobs are safer for someone like me?",
  "Show me paths that take less than 3 months",
  "How many BPO jobs are in Indore right now?",
  "मुझे क्या करना चाहिए?",
];

/* ═══════════════════════════════════════════════════════════════════════
   TYPEWRITER HOOK
   ═══════════════════════════════════════════════════════════════════════ */

function useTypewriter(text, speed = 14) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!text) {
      setDisplayed("");
      setDone(true);
      return;
    }
    setDisplayed("");
    setDone(false);
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(interval);
        setDone(true);
      }
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);

  return { displayed, done };
}

/* ═══════════════════════════════════════════════════════════════════════
   CHAT BUBBLE
   ═══════════════════════════════════════════════════════════════════════ */

function ChatBubble({ message, isTyping }) {
  const isAI = message.role === "ai";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-2.5 ${isAI ? "" : "flex-row-reverse"}`}
    >
      {/* Avatar */}
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5"
        style={{
          background: isAI ? "rgba(151,168,122,0.12)" : "rgba(218,215,205,0.08)",
          border: `1px solid ${isAI ? "rgba(151,168,122,0.25)" : "rgba(218,215,205,0.15)"}`,
        }}
      >
        {isAI ? (
          <Bot size={13} style={{ color: "#97A87A" }} />
        ) : (
          <User size={13} style={{ color: "#dad7cd" }} />
        )}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${isAI ? "rounded-tl-md" : "rounded-tr-md"}`}
        style={{
          background: isAI ? "rgba(151,168,122,0.10)" : "rgba(218,215,205,0.10)",
          border: `1px solid ${isAI ? "rgba(151,168,122,0.20)" : "rgba(218,215,205,0.20)"}`,
        }}
      >
        <p
          className="font-data text-[13px] leading-relaxed whitespace-pre-line"
          style={{ color: "#dad7cd" }}
        >
          {message.text}
          {isTyping && (
            <motion.span
              className="inline-block ml-1 w-[2px] h-[14px] align-middle"
              style={{ background: "#97A87A" }}
              animate={{ opacity: [1, 0] }}
              transition={{ repeat: Infinity, duration: 0.6 }}
            />
          )}
        </p>
      </div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   FRAMER VARIANTS – Staggered suggestion pills
   ═══════════════════════════════════════════════════════════════════════ */

const pillContainer = {
  initial: {},
  animate: { transition: { staggerChildren: 0.09, delayChildren: 0.35 } },
};

const pillItem = {
  initial: { opacity: 0, y: 12, scale: 0.95 },
  animate: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.35, ease: "easeOut" } },
};

/* ═══════════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   Single centered column — no sidebar, ChatGPT/Gemini style
   ═══════════════════════════════════════════════════════════════════════ */

const IntelligenceChatbot = ({ profileId }) => {
  const [messages, setMessages] = useState([]);
  const [typingText, setTypingText] = useState(null);
  const [isWaiting, setIsWaiting] = useState(false);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const { displayed, done } = useTypewriter(typingText, 14);

  /* ── Commit the AI message once typewriter finishes ── */
  useEffect(() => {
    if (done && typingText) {
      setMessages((prev) => [...prev, { id: Date.now(), role: "ai", text: typingText }]);
      setTypingText(null);
    }
  }, [done, typingText]);

  /* ── Auto-scroll ── */
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, displayed]);

  /* ── Send handler — calls real backend API ── */
  const handleSend = useCallback(
    async (text) => {
      const msg = (text || input).trim();
      if (!msg || typingText || isWaiting) return;
      setInput("");
      setMessages((prev) => [...prev, { id: Date.now(), role: "user", text: msg }]);
      setIsWaiting(true);

      try {
        // Build history from messages for context
        const history = messages.map((m) => ({
          role: m.role === "ai" ? "assistant" : "user",
          content: m.text,
        }));

        const response = await sendChatMessage({
          message: msg,
          profileId: profileId || null,
          history,
        });
        setTypingText(response.reply);
      } catch {
        setTypingText("I'm having trouble connecting to the server. Please try again in a moment.");
      } finally {
        setIsWaiting(false);
      }
    },
    [input, typingText, isWaiting, messages, profileId],
  );

  const isEmpty = messages.length === 0 && !typingText;

  /* ─────────────────────────────────────────────────────────────────── */

  return (
    <div className="h-[calc(100vh-80px)] flex flex-col mx-auto w-full max-w-3xl px-4 py-4">
      {/* ── Glassmorphic container ── */}
      <div
        className="flex-1 flex flex-col rounded-2xl overflow-hidden"
        style={{
          background: "rgba(26,29,26,0.60)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          border: "1px solid rgba(151,168,122,0.20)",
        }}
      >
        {/* ── Scrollable chat area ── */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-6 custom-scroll">
          {isEmpty ? (
            /* ════════ EMPTY STATE ════════ */
            <div className="flex flex-col items-center justify-center h-full select-none">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col items-center text-center mb-10"
              >
                {/* Icon */}
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5"
                  style={{
                    background: "rgba(151,168,122,0.12)",
                    border: "1px solid rgba(151,168,122,0.25)",
                  }}
                >
                  <Sparkles size={24} style={{ color: "#97A87A" }} />
                </div>

                <h2
                  className="font-brand text-xl mb-2"
                  style={{ color: "#dad7cd", fontWeight: 700 }}
                >
                  Hello! I'm the Oasis Intelligence Assistant.
                </h2>
                <p className="font-data text-sm max-w-md" style={{ color: "#6B7265" }}>
                  How can I help you navigate the market today?
                </p>
              </motion.div>

              {/* ── YouTube-style Suggestion Pills ── */}
              <motion.div
                variants={pillContainer}
                initial="initial"
                animate="animate"
                className="flex flex-wrap justify-center gap-2.5 max-w-xl"
              >
                {SUGGESTIONS.map((s) => (
                  <motion.button
                    key={s}
                    variants={pillItem}
                    onClick={() => handleSend(s)}
                    className="rounded-full px-5 py-2.5 text-sm font-data cursor-pointer transition-all"
                    style={{
                      color: "#dad7cd",
                      background: "rgba(218,215,205,0.10)",
                      border: "1px solid rgba(151,168,122,0.30)",
                    }}
                    whileHover={{
                      scale: 1.04,
                      backgroundColor: "rgba(218,215,205,0.20)",
                      borderColor: "rgba(151,168,122,0.55)",
                    }}
                    whileTap={{ scale: 0.97 }}
                  >
                    {s}
                  </motion.button>
                ))}
              </motion.div>
            </div>
          ) : (
            /* ════════ MESSAGE LIST ════════ */
            <div className="space-y-4">
              <AnimatePresence>
                {messages.map((m) => (
                  <ChatBubble key={m.id} message={m} />
                ))}
              </AnimatePresence>

              {/* Live typewriter bubble */}
              {typingText && (
                <ChatBubble
                  message={{ id: "typing", role: "ai", text: displayed }}
                  isTyping={!done}
                />
              )}
            </div>
          )}
        </div>

        {/* ── Pinned input bar ── */}
        <div className="px-4 pb-4 pt-2">
          <div
            className="flex items-center gap-3 rounded-xl px-4 py-3"
            style={{
              background: "rgba(218,215,205,0.06)",
              border: "1px solid rgba(151,168,122,0.18)",
            }}
          >
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask about reskilling, risk scores, or market trends…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              className="flex-1 bg-transparent text-sm font-data placeholder:opacity-30 outline-none"
              style={{ color: "#dad7cd" }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || !!typingText || isWaiting}
              className="p-2 rounded-lg transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
              style={{ background: "rgba(151,168,122,0.15)" }}
              onMouseEnter={(e) => {
                if (!e.currentTarget.disabled)
                  e.currentTarget.style.background = "rgba(151,168,122,0.30)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(151,168,122,0.15)";
              }}
            >
              {isWaiting ? (
                <Loader2 size={15} className="animate-spin" style={{ color: "#97A87A" }} />
              ) : (
                <Send size={15} style={{ color: "#97A87A" }} />
              )}
            </button>
          </div>

          <p className="text-center font-data text-[10px] mt-2.5 opacity-60" style={{ color: "#6B7265" }}>
            Responses generated from Oasis market data &amp; government skill databases. Always verify
            with your local skill centre.
          </p>
        </div>
      </div>
    </div>
  );
};

export default IntelligenceChatbot;
