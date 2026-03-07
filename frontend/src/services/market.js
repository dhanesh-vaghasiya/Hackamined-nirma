import api from "./api";

export const triggerScrape = async ({ keywords, location, max_rows } = {}) => {
  const body = {};
  if (keywords) body.keywords = keywords;
  if (location) body.location = location;
  if (max_rows) body.max_rows = max_rows;
  const { data } = await api.post("/scraper/scrape-and-update", body, { timeout: 300000 });
  return data;
};

export const getMarketSummary = async () => {
  const { data } = await api.get("/market/summary");
  return data;
};

export const getHiringTrends = async ({ limit = 60, city = "all-india", timeframe = "1yr" } = {}) => {
  const params = new URLSearchParams({ limit, city, timeframe });
  const { data } = await api.get(`/market/hiring-trends?${params}`);
  return data;
};

export const getSkillsIntel = async ({ city = "all-india", timeframe = "1yr" } = {}) => {
  const params = new URLSearchParams({ city, timeframe });
  const { data } = await api.get(`/market/skills-intel?${params}`);
  return data;
};

export const getAiVulnerability = async ({ city = "all-india" } = {}) => {
  const params = new URLSearchParams({ city });
  const { data } = await api.get(`/market/ai-vulnerability?${params}`);
  return data;
};

export const getAvailableSkills = async () => {
  const { data } = await api.get("/market/available-skills");
  return data;
};

export const getSkillGap = async ({ skills = [], city = "all-india" } = {}) => {
  const { data } = await api.post("/market/skill-gap", { skills, city });
  return data;
};

export const getJobRoles = async ({ q = "", limit = 100 } = {}) => {
  const params = new URLSearchParams({ q, limit });
  const { data } = await api.get(`/market/job-roles?${params}`);
  return data;
};

export const getJobRoleSkills = async (role) => {
  const params = new URLSearchParams({ role });
  const { data } = await api.get(`/market/job-role-skills?${params}`);
  return data;
};

export const getSkillTrend = async ({ skill = "", city = "all-india" } = {}) => {
  const params = new URLSearchParams({ skill, city });
  const { data } = await api.get(`/market/skill-trend?${params}`);
  return data;
};

export const getCities = async () => {
  const { data } = await api.get("/market/cities");
  return data;
};

export const getMarketRecords = async ({ page = 1, pageSize = 100, city = "all-india", q = "" } = {}) => {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  if (city) params.set("city", city);
  if (q) params.set("q", q);

  const { data } = await api.get(`/market/records?${params.toString()}`);
  return data;
};

/* ── Employer View APIs ── */

export const getEmployerCitySkills = async ({ city = "all-india" } = {}) => {
  const params = new URLSearchParams({ city });
  const { data } = await api.get(`/market/employer/city-skills?${params}`);
  return data;
};

export const getEmployerSectorHiring = async ({ city = "all-india" } = {}) => {
  const params = new URLSearchParams({ city });
  const { data } = await api.get(`/market/employer/sector-hiring?${params}`);
  return data;
};
