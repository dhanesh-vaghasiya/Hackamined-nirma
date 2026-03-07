import { useEffect, useState } from "react";

const UserProfile = () => {

  const [data, setData] = useState(null);

  useEffect(() => {

    const token = localStorage.getItem("token");

    fetch("http://localhost:5000/api/me", {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then(res => res.json())
      .then(data => setData(data));

  }, []);

  if (!data) return <p>Loading...</p>;

  return (
    <div className="min-h-screen pt-24 pb-12 px-6 flex justify-center text-white">
      <div className="w-full max-w-3xl space-y-8">

        {/* Header Section */}
        <div className="glass-card-solid p-6 rounded-2xl">
          <h1 className="text-3xl font-brand font-bold" style={{ color: "var(--color-oasis-forest)" }}>
            {data.user.name}
          </h1>
          <p className="font-data opacity-70 mt-1">{data.user.email}</p>
        </div>

        {/* Info Grid */}
        <div className="grid grid-cols-1 md://grid-cols-2 gap-6">

          <div className="glass-card p-6 rounded-xl">
            <h3 className="text-sm font-data opacity-60 uppercase tracking-widest mb-2">Job Title</h3>
            <p className="text-xl font-brand font-semibold">{data.profile?.job_title || "Not specified"}</p>
          </div>

          <div className="glass-card p-6 rounded-xl">
            <h3 className="text-sm font-data opacity-60 uppercase tracking-widest mb-2">Experience</h3>
            <p className="text-xl font-brand font-semibold">
              {data.profile?.experience_years !== null && data.profile?.experience_years !== undefined
                ? `${data.profile.experience_years} years`
                : "Not specified"}
            </p>
          </div>

          <div className="glass-card p-6 rounded-xl md:col-span-2">
            <h3 className="text-sm font-data opacity-60 uppercase tracking-widest mb-3">Skills</h3>
            {data.profile?.skills && data.profile.skills.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {data.profile.skills.map((s, i) => (
                  <span key={i} className="px-3 py-1 text-sm font-data rounded-full border"
                    style={{ borderColor: "var(--color-oasis-border)", backgroundColor: "var(--color-oasis-card)" }}>
                    {s}
                  </span>
                ))}
              </div>
            ) : (
              <p className="font-data opacity-60 italic">No skills listed</p>
            )}
          </div>

          <div className="glass-card p-6 rounded-xl md:col-span-2 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-data opacity-60 uppercase tracking-widest mb-1">AI Risk Score</h3>
              <p className="text-2xl font-brand font-bold" style={{ color: "var(--color-oasis-forest)" }}>
                {data.risk?.score ?? "N/A"}
              </p>
            </div>
            <div className="text-right">
              <span className="px-4 py-2 font-data text-sm font-semibold rounded-lg"
                style={{ backgroundColor: "rgba(151,168,122,0.15)", color: "var(--color-oasis-forest)" }}>
                {data.risk?.level ?? "N/A"}
              </span>
            </div>
          </div>

        </div>
      </div>
    </div>
  );

};

export default UserProfile;