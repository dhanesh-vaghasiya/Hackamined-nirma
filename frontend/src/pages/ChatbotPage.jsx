import IntelligenceChatbot from "../components/worker/IntelligenceChatbot";

/* ═══════════════════════════════════════════════════════════════════════
   CHATBOT PAGE
   Thin wrapper rendered by Dashboard when activeLayer === "AI Assistant"
   All layout / glass / pills live inside IntelligenceChatbot itself.
   ═══════════════════════════════════════════════════════════════════════ */

const ChatbotPage = ({ profileId }) => <IntelligenceChatbot profileId={profileId} />;

export default ChatbotPage;
