import api from "./api";

export const analyzeWorkerProfile = async (payload) => {
  const { data } = await api.post("/career/analyze", payload);
  return data;
};

export const generateRoadmap = async (payload) => {
  const { data } = await api.post("/roadmap/generate", payload, {
    timeout: 120_000,
  });
  return data;
};
