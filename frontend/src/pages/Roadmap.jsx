import { useState } from "react";
import api from "../services/api";
import "./Roadmap.css";

const SAMPLE_PROFILES = [
  { job_title: "Data Entry Operator", city: "Ahmedabad", experience: 3, description: "I do data entry in Excel and some basic Tally work.", user_id: 1 },
  { job_title: "Junior Accountant", city: "Mumbai", experience: 5, description: "I handle bookkeeping, GST returns, and use Tally and QuickBooks.", user_id: 2 },
  { job_title: "Customer Support Executive", city: "Bangalore", experience: 2, description: "I work in voice-based tech support for a SaaS product.", user_id: 3 },
  { job_title: "Content Writer", city: "Pune", experience: 4, description: "I write SEO blogs, social media posts, and use WordPress and Canva.", user_id: 4 },
  { job_title: "Warehouse Supervisor", city: "Delhi", experience: 7, description: "I manage warehouse inventory with WMS and handle dispatches.", user_id: 5 },
];

const Roadmap = () => {
  const [form, setForm] = useState({ job_title: "", city: "", experience: "", description: "", user_id: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const fillSample = (profile) => {
    setForm({
      job_title: profile.job_title,
      city: profile.city,
      experience: String(profile.experience),
      description: profile.description,
      user_id: String(profile.user_id || ""),
    });
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        job_title: form.job_title,
        city: form.city,
        experience: Number(form.experience) || 0,
        description: form.description,
      };
      if (form.user_id) payload.user_id = Number(form.user_id);

      const { data } = await api.post("/roadmap/generate", payload);
      setResult(data.data);
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const recommendation = result?.recommended_skill || {};
  const finalRoadmap = result?.final_roadmap || result?.structured_roadmap || {};
  const stages = finalRoadmap?.stages || [];
  const nptelCourses = result?.nptel_courses || [];

  return (
    <div className="roadmap-page page">
      <h1>AI Roadmap Generator</h1>

      {/* ── Input Form ──────────────────────────────── */}
      <div className="roadmap-form">
        <h2>Your Profile</h2>

        <div style={{ marginBottom: "1rem" }}>
          <label style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.3rem", display: "block" }}>
            Quick fill from samples:
          </label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {SAMPLE_PROFILES.map((p) => (
              <button
                key={p.user_id}
                type="button"
                onClick={() => fillSample(p)}
                style={{
                  padding: "0.3rem 0.8rem", fontSize: "0.8rem", borderRadius: "20px",
                  border: "1px solid var(--color-border, #dee2e6)", background: "var(--color-bg, #fff)",
                  cursor: "pointer", color: "var(--color-text, #333)",
                }}
              >
                {p.job_title}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-group">
              <label>Job Title</label>
              <input name="job_title" value={form.job_title} onChange={handleChange} placeholder="e.g. Data Entry Operator" required />
            </div>
            <div className="form-group">
              <label>City</label>
              <input name="city" value={form.city} onChange={handleChange} placeholder="e.g. Ahmedabad" required />
            </div>
            <div className="form-group">
              <label>Years of Experience</label>
              <input name="experience" type="number" min="0" value={form.experience} onChange={handleChange} placeholder="e.g. 3" required />
            </div>
            <div className="form-group">
              <label>User ID (optional, for dummy data)</label>
              <input name="user_id" type="number" min="1" max="5" value={form.user_id} onChange={handleChange} placeholder="1-5" />
            </div>
            <div className="form-group full-width">
              <label>Work Description</label>
              <textarea name="description" value={form.description} onChange={handleChange} placeholder="Describe what you do at work..." required />
            </div>
          </div>
          <button className="generate-btn" type="submit" disabled={loading}>
            {loading ? "Generating..." : "Generate Roadmap"}
          </button>
        </form>
      </div>

      {/* ── Loading ─────────────────────────────────── */}
      {loading && (
        <div className="loading-overlay">
          <div className="spinner" />
          <p>AI agent is analyzing your profile, gathering market data, and building your personalized roadmap...</p>
        </div>
      )}

      {/* ── Error ──────────────────────────────────── */}
      {error && <div className="error-box">Error: {error}</div>}

      {/* ── Results ─────────────────────────────────── */}
      {result && !loading && (
        <>
          {/* Step 1: User Profile */}
          <div className="pipeline-section">
            <h2><span className="step-badge">1</span> User Profile</h2>
            <div className="data-grid">
              <div className="data-card">
                <h4>Profile Input</h4>
                <pre>{JSON.stringify(result.user_profile, null, 2)}</pre>
              </div>
            </div>
          </div>

          {/* Step 2: Data Retrieved */}
          <div className="pipeline-section">
            <h2><span className="step-badge">2</span> Data Retrieved from System</h2>
            <div className="data-grid">
              {Object.entries(result.data_retrieved || {}).map(([key, val]) => (
                <div className="data-card" key={key}>
                  <h4>{key}</h4>
                  <pre>{JSON.stringify(val, null, 2)}</pre>
                </div>
              ))}
            </div>
          </div>

          {/* Step 3: Skill Recommendation */}
          <div className="pipeline-section">
            <h2><span className="step-badge">3</span> AI Skill Recommendation</h2>
            <div className="skill-recommendation">
              <div className="skill-name">{recommendation.recommended_skill || "—"}</div>
              {recommendation.reasoning && <p className="reasoning">{recommendation.reasoning}</p>}
              {recommendation.risk_assessment && (
                <p className="reasoning" style={{ marginTop: "0.5rem" }}>
                  <strong>Risk: </strong>{recommendation.risk_assessment}
                </p>
              )}
              {recommendation.growth_potential && (
                <p className="reasoning" style={{ marginTop: "0.3rem" }}>
                  <strong>Growth: </strong>{recommendation.growth_potential}
                </p>
              )}
            </div>
          </div>

          {/* Step 4: Raw Roadmap */}
          <div className="pipeline-section">
            <h2><span className="step-badge">4</span> Raw Roadmap (from Roadman API)</h2>
            <div className="raw-output">
              <pre>{JSON.stringify(result.raw_roadmap, null, 2)}</pre>
            </div>
          </div>

          {/* Step 5: Structured Roadmap */}
          <div className="pipeline-section">
            <h2><span className="step-badge">5</span> Structured Learning Roadmap</h2>
            {finalRoadmap.summary && (
              <p style={{ marginBottom: "1rem", fontSize: "0.95rem", lineHeight: 1.5 }}>
                {finalRoadmap.summary}
              </p>
            )}
            {finalRoadmap.total_duration && (
              <p style={{ marginBottom: "1rem", fontSize: "0.9rem", color: "var(--color-text-secondary, #888)" }}>
                Total Duration: <strong>{finalRoadmap.total_duration}</strong>
              </p>
            )}
            <div className="stages-timeline">
              {stages.map((stage, i) => (
                <div className="stage-item" key={i}>
                  <h3>Stage {stage.stage_number || i + 1}: {stage.name}</h3>
                  <div className="stage-duration">{stage.duration}</div>
                  <p className="stage-desc">{stage.description}</p>
                  {stage.topics && stage.topics.length > 0 && (
                    <div className="stage-topics">
                      {stage.topics.map((t, j) => <span className="topic-tag" key={j}>{t}</span>)}
                    </div>
                  )}
                  {stage.recommended_courses && stage.recommended_courses.length > 0 && (
                    <div className="course-list" style={{ marginTop: "0.5rem" }}>
                      {stage.recommended_courses.map((c, k) => (
                        <div className="course-card" key={k}>
                          <h4>{c.title}</h4>
                          <div className="course-meta">{c.institution} &middot; {c.duration}</div>
                          {c.url && <a href={c.url} target="_blank" rel="noopener noreferrer">View Course &rarr;</a>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Step 6: NPTEL Courses */}
          <div className="pipeline-section">
            <h2><span className="step-badge">6</span> NPTEL Course Recommendations</h2>
            <div className="course-list">
              {nptelCourses.length > 0 ? (
                nptelCourses.map((c, i) => (
                  <div className="course-card" key={i}>
                    <h4>{c.title}</h4>
                    <div className="course-meta">
                      {c.institution}{c.instructor ? ` • ${c.instructor}` : ""} &middot; {c.duration}
                    </div>
                    {c.url && <a href={c.url} target="_blank" rel="noopener noreferrer">View on NPTEL &rarr;</a>}
                  </div>
                ))
              ) : (
                <p style={{ color: "var(--color-text-secondary, #888)" }}>No NPTEL courses found.</p>
              )}
            </div>
          </div>

          {/* Career Impact */}
          {finalRoadmap.career_impact && (
            <div className="pipeline-section">
              <h2><span className="step-badge">&#10003;</span> Career Impact</h2>
              <p style={{ fontSize: "0.95rem", lineHeight: 1.5 }}>{finalRoadmap.career_impact}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Roadmap;
