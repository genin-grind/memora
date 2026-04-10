import { motion } from "framer-motion";

export default function HeroPanel({ title, eyebrow, description, children }) {
  return (
    <motion.section
      className="hero-panel"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
    >
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p className="hero-description">{description}</p>
      {children}
    </motion.section>
  );
}
