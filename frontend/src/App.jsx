import { useMemo, useState } from "react";
import DashboardLayout from "./layout/DashboardLayout";
import HiringTrends from "./pages/HiringTrends";
import SkillsIntelligence from "./pages/SkillsIntelligence";
import AIRiskIndex from "./pages/AIRiskIndex";

const tabs = [
  { key: "hiring", label: "Hiring Trends" },
  { key: "skills", label: "Skills Intelligence" },
  { key: "ai", label: "AI Risk Index" },
];

function TabContent({ active }) {
  if (active === "skills") return <SkillsIntelligence />;
  if (active === "ai") return <AIRiskIndex />;
  return <HiringTrends />;
}

export default function App() {
  const [activeTab, setActiveTab] = useState("hiring");

  const live = useMemo(() => true, []);

  return (
    <DashboardLayout tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} isLive={live}>
      <div key={activeTab} className="animate-fadeInUp">
        <TabContent active={activeTab} />
      </div>
    </DashboardLayout>
  );
}
