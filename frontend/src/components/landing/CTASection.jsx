import { Link } from "react-router-dom";
import { motion } from "framer-motion";

const CTASection = ({ user }) => {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.6 }}
      transition={{ duration: 0.45 }}
      className="mt-10 flex flex-col items-center"
    >
      <Link
        to={user ? "/dashboard" : "/register"}
        className="rounded-xl border border-[#9fe87088] bg-[#9fe870] px-10 py-3.5 font-brand text-[15px] font-bold uppercase tracking-[0.06em] text-black transition-all duration-200 hover:shadow-[0_0_36px_rgba(159,232,112,0.52)]"
      >
        START YOUR FREE ANALYSIS
      </Link>
      <p className="mt-5 max-w-2xl text-center font-data text-[11px] leading-relaxed text-[#7a857a]">
        Responses generated from Oasis market data and government skill databases. Always verify with your local skill mentor.
      </p>
    </motion.section>
  );
};

export default CTASection;
