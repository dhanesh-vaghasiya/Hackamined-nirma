import api from "./api";

export const analyzeWorkerProfile = async (payload) => {
  const { data } = await api.post("/career/analyze", payload);
  return data;
};
