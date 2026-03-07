import { motion } from "framer-motion";

const FeatureCard = ({ icon: Icon, title, description, delay = 0 }) => {
  return (
    <motion.article
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.35 }}
      transition={{ duration: 0.45, delay }}
      whileHover={{ y: -4, scale: 1.01 }}
      className="rounded-2xl border border-[#9fe87025] bg-[#0c120f70] p-5 backdrop-blur-md"
    >
      <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl border border-[#9fe87038] bg-[#0e13115f] text-[#c8f4a2]">
        <Icon size={20} strokeWidth={1.8} />
      </div>
      <h3 className="font-brand text-lg font-bold leading-snug text-white">{title}</h3>
      <p className="mt-2 font-data text-[13px] leading-relaxed text-[#a4aea0]">{description}</p>
    </motion.article>
  );
};

export default FeatureCard;
