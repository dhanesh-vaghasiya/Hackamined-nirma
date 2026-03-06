import { motion } from "framer-motion";

/**
 * Oasis-themed glass card with optional glow border on hover.
 *
 * Props:
 *   - children, className, style — standard
 *   - glow  — show forest-green glow on hover (default true)
 *   - delay — entrance animation delay
 */
export default function GlassCard({
  children,
  className = "",
  style = {},
  glow = true,
  delay = 0,
  ...rest
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
      className={`glass-card p-5 ${className}`}
      style={style}
      {...rest}
    >
      {children}
    </motion.div>
  );
}
