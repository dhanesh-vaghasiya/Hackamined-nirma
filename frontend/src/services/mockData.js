const cities = [
  "Bengaluru",
  "Hyderabad",
  "Pune",
  "Mumbai",
  "Delhi",
  "Chennai",
  "Ahmedabad",
  "Jaipur",
  "Lucknow",
  "Kochi",
  "Indore",
  "Bhopal",
  "Coimbatore",
  "Bhubaneswar",
  "Chandigarh",
  "Nagpur",
  "Vadodara",
  "Surat",
  "Mysuru",
  "Patna",
  "Kanpur",
  "Vijayawada",
  "Ranchi",
  "Guwahati",
];

const categories = ["Data Analyst", "Software Engineer", "BPO Voice", "Data Entry", "AI Engineer"];

const random = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

const buildDates = (points = 20) =>
  Array.from({ length: points }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - (points - index));
    return date.toISOString().slice(5, 10);
  });

export const mockData = {
  "/api/hiring-trends/time-series": () => {
    const dates = buildDates(30);
    const job_counts = dates.map(() => random(2100, 5500));
    return { dates, job_counts };
  },
  "/api/hiring-trends/categories": () =>
    categories.map((category) => ({ category, count: random(600, 3800) })),
  "/api/hiring-trends/cities": () => cities.map((city) => ({ city, count: random(180, 3400) })),
  "/api/jobs": () =>
    Array.from({ length: 46 }, (_, idx) => ({
      title: ["Data Analyst", "Software Engineer", "BPO Voice Executive", "Data Entry Specialist", "AI Engineer"][idx % 5],
      company: ["Infosys", "TCS", "Wipro", "Accenture", "Tech Mahindra", "Capgemini"][idx % 6],
      city: cities[idx % cities.length],
      salary_range: ["3-5 LPA", "5-8 LPA", "8-12 LPA", "12-18 LPA"][idx % 4],
      posting_date: buildDates(46)[idx],
      source: idx % 2 === 0 ? "LinkedIn" : "Naukri",
    })),

  "/api/skills/rising": () =>
    [
      "LangChain",
      "Prompt Engineering",
      "MLOps",
      "Agentic AI",
      "Vector Databases",
      "PySpark",
      "Power BI",
      "FastAPI",
      "Snowflake",
      "RAG",
      "dbt",
      "Kubernetes",
      "Azure OpenAI",
      "LLM Evaluation",
      "Data Governance",
      "NLP",
      "Tableau",
      "GitOps",
      "Feature Stores",
      "MLflow",
    ].map((skill) => ({ skill, growth: random(8, 42) })),
  "/api/skills/declining": () =>
    [
      "Manual Testing",
      "Legacy ETL",
      "Basic Excel",
      "Cold Calling",
      "Manual Data Entry",
      "Flash",
      "jQuery",
      "Monolithic Java",
      "On-Prem BI",
      "Basic SEO",
      "Waterfall PM",
      "VBScript",
      "Telecalling",
      "Legacy CMS",
      "Non-Cloud Admin",
      "OCR Review",
      "Desktop Support",
      "Fax Operations",
      "Invoice Typing",
      "Data Labeling Basic",
    ].map((skill) => ({ skill, decline: random(5, 38) })),
  "/api/skills/gap": () =>
    [
      "Data Analytics",
      "AI Engineering",
      "Cloud Security",
      "MLOps",
      "Cybersecurity",
      "Prompt Engineering",
      "UI/UX",
      "DevOps",
      "Product Analytics",
      "Data Engineering",
    ].map((skill) => {
      const market_demand = random(4000, 18000);
      const training_supply = random(1200, 9000);
      return { skill, market_demand, training_supply };
    }),
  "/api/ai-risk": () =>
    Array.from({ length: 36 }, (_, idx) => {
      const score = random(8, 97);
      let risk_category = "Low";
      if (score > 75) risk_category = "Critical";
      else if (score > 50) risk_category = "High";
      else if (score > 25) risk_category = "Medium";

      return {
        role: ["BPO Voice", "Data Entry", "Data Analyst", "Software Engineer", "HR Recruiter", "Graphic Designer"][idx % 6],
        city: cities[idx % cities.length],
        ai_risk_score: score,
        risk_category,
        hiring_trend: ["Rising", "Stable", "Declining"][idx % 3],
      };
    }),
  "/api/ai-risk/cities": () => cities.map((city) => ({ city, risk: random(12, 95) })),
  "/api/ai-risk/trends": () => {
    const dates = buildDates(20);
    return dates.map((date) => ({ date, score: random(28, 82) }));
  },
};
