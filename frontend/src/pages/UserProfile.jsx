import { useEffect, useState } from "react";
import WorkerResultsUI, { EmptyState } from "../components/worker/WorkerResultsUI";

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

  if (!data) return <p className="pt-24 text-center text-white opacity-60">Loading profile data...</p>;

  // Check if profile actually has an ID, meaning a WorkerProfile was generated for this user
  const hasProfile = !!data.profile?.id;

  return (
    <div className="min-h-screen pt-24 pb-12 px-6 flex justify-center text-white">
      <div className="w-full max-w-5xl space-y-8 h-full flex flex-col">

        {/* Header Section */}
        <div className="glass-card-solid p-6 rounded-2xl shrink-0">
          <h1 className="text-3xl font-brand font-bold" style={{ color: "var(--color-oasis-forest)" }}>
            {data.user.name}
          </h1>
          <p className="font-data opacity-70 mt-1">{data.user.email}</p>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 min-h-[500px]">
          {hasProfile ? (
            <WorkerResultsUI
              analysis={data.analysis}
              profile={data.profile}
              profileId={data.profile?.id}
            />
          ) : (
            <div className="glass-card rounded-2xl h-full flex flex-col items-center justify-center p-8 text-center min-h-[400px]">
              <EmptyState />
              <p className="mt-4 font-data text-sm opacity-60 max-w-md">
                You haven't generated a worker profile yet. Head over to the Worker Portal on the dashboard to analyze your career and generate a risk roadmap!
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );

};

export default UserProfile;