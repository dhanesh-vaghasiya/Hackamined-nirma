import api from "./api";

export const sendChatMessage = async ({ message, profileId, history }) => {
  const { data } = await api.post("/chatbot/chat", {
    message,
    profile_id: profileId || null,
    history: history || [],
  });
  return data;
};

export const getChatHistory = async (profileId) => {
  const params = profileId ? `?profile_id=${profileId}` : "";
  const { data } = await api.get(`/chatbot/history${params}`);
  return data;
};

export const getLatestInsightDeck = async () => {
  const { data } = await api.get("/chatbot/insight-deck");
  return data;
};

export const getInsightDecks = async (limit = 10) => {
  const { data } = await api.get(`/chatbot/insight-decks?limit=${limit}`);
  return data;
};
