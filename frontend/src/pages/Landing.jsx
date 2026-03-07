import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/landing/Navbar";
import Hero from "../components/landing/Hero";
import CTASection from "../components/landing/CTASection";

const Landing = () => {
  const { user } = useAuth();

  return (
    <div
      className="relative min-h-screen overflow-hidden pb-16"
      style={{
        backgroundImage: 'url("/in2.png")',
        backgroundSize: "cover",
        backgroundPosition: "center top",
        backgroundRepeat: "no-repeat",
      }}
    >
      {/* Left-side dark overlay for text readability; fades out toward the India map area */}
      <div
        className="pointer-events-none absolute inset-0 z-[1]"
        style={{
          background:
            "linear-gradient(to right, rgba(3,5,4,0.92) 0%, rgba(3,5,4,0.82) 30%, rgba(3,5,4,0.45) 52%, rgba(3,5,4,0.08) 68%, transparent 82%)",
        }}
      />
      {/* Top & bottom vignette for depth */}
      <div
        className="pointer-events-none absolute inset-0 z-[1]"
        style={{
          background:
            "linear-gradient(180deg, rgba(3,5,4,0.30) 0%, transparent 18%, transparent 78%, rgba(3,5,4,0.50) 100%)",
        }}
      />

      <div className="relative z-10 mx-auto max-w-[1580px] px-6 md:px-12 lg:px-16">
        <Navbar user={user} />

        <motion.main
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Hero user={user} />
          <CTASection user={user} />
        </motion.main>
      </div>
    </div>
  );
};

export default Landing;
