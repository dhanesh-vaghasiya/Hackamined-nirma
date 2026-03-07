import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, ChartNoAxesColumnIncreasing, GitPullRequestArrow, Radar } from "lucide-react";
import FeatureCard from "./FeatureCard";
import TrustedRow from "./TrustedRow";

const cards = [
  {
    icon: ChartNoAxesColumnIncreasing,
    title: "Real-Time Market Demand",
    description: "understand skill trends across India.",
  },
  {
    icon: GitPullRequestArrow,
    title: "Skill Vulnerability & Pathing",
    description: "identify risk and build routes.",
  },
  {
    icon: Radar,
    title: "Workforce Talent Insights",
    description: "data-driven hiring and planning.",
  },
];

const Hero = ({ user }) => {
  return (
    <section className="mt-2">
      {/* Content is constrained to the left ~46% so the India map in the background stays fully unobstructed */}
      <motion.div
        initial={{ opacity: 0, y: 22 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="pt-3 lg:max-w-[46%]"
      >
        <h1 className="font-brand text-[46px] font-bold uppercase leading-[0.90] tracking-[-0.02em] text-[#ffffff] sm:text-[54px] lg:text-[68px]">
          NAVIGATE
          <br />
          INDIA'S TALENT
          <br />
          LANDSCAPE.
          <br />
          DECIPHER THE
          <br />
          SKILLS OF
          <br />
          TOMORROW.
        </h1>
        <p className="mt-6 max-w-[480px] font-data text-[15px] leading-[1.52] text-[#8fa68f] md:text-[16px]">
          Discover critical skill gaps, identify high-demand roles, and optimize workforce planning with Oasis's real-time, predictive intelligence platform.
        </p>

        <Link
          to={user ? "/dashboard" : "/register"}
          className="mt-7 inline-flex items-center gap-2.5 rounded-lg border border-[#9fe87088] bg-transparent px-7 py-3 font-brand text-[13px] font-bold uppercase tracking-[0.08em] text-[#d8f0c8] transition-all duration-200 hover:border-[#9fe870bb] hover:bg-[#9fe8700f]"
        >
          EXPLORE MARKET INTEL <ArrowRight size={17} strokeWidth={2.5} />
        </Link>

        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {cards.map((card, idx) => (
            <FeatureCard
              key={card.title}
              icon={card.icon}
              title={card.title}
              description={card.description}
              delay={0.18 + idx * 0.08}
            />
          ))}
        </div>

        <TrustedRow />
      </motion.div>
    </section>
  );
};

export default Hero;
