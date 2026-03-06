import api from "./api";

export const analyzeWorkerProfile = async (payload) => {
  const { data } = await api.post("/career/analyze", payload);
  return data;
};

export const generateRoadmap = async (profileId, chosenRole) => {
  const { data } = await api.post("/career/roadmap", {
    profile_id: profileId,
    chosen_role: chosenRole,
  });
  return data;
};
