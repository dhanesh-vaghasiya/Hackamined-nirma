import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, RotateCcw, X, GraduationCap } from "lucide-react";

export default function FlashcardView({ flashcards, topic, onClose }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [direction, setDirection] = useState(0);

  if (!flashcards || flashcards.length === 0) return null;

  const currentCard = flashcards[currentIndex];

  const handleNext = () => {
    if (currentIndex < flashcards.length - 1) {
      setDirection(1);
      setIsFlipped(false);
      setTimeout(() => setCurrentIndex((prev) => prev + 1), 150);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setDirection(-1);
      setIsFlipped(false);
      setTimeout(() => setCurrentIndex((prev) => prev - 1), 150);
    }
  };

  const flipCard = () => {
    setIsFlipped(!isFlipped);
  };

  // Animation variants for the card sliding in/out
  const slideVariants = {
    enter: (dir) => ({
      x: dir > 0 ? 50 : -50,
      opacity: 0,
    }),
    center: {
      zIndex: 1,
      x: 0,
      opacity: 1,
    },
    exit: (dir) => ({
      zIndex: 0,
      x: dir < 0 ? 50 : -50,
      opacity: 0,
    }),
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="sc-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      style={{ zIndex: 100 }}
    >
      <motion.div
        className="sc-panel oasis-dash-card flex flex-col items-center justify-between"
        initial={{ y: 30, scale: 0.95 }}
        animate={{ y: 0, scale: 1 }}
        exit={{ y: 30, scale: 0.95 }}
        onClick={(e) => e.stopPropagation()}
        style={{ width: "450px", height: "350px", overflow: "hidden", position: "relative" }}
      >
        {/* Header */}
        <div className="w-full flex items-center justify-between p-4 border-b border-[#30362A]/30">
          <div className="flex items-center gap-2">
            <GraduationCap size={16} style={{ color: "#D4A853" }} />
            <h4 className="font-brand text-sm" style={{ color: "#dad7cd", fontWeight: 600 }}>
              {topic} Flashcards
            </h4>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
          >
            <X size={16} style={{ color: "#6B7265" }} />
          </button>
        </div>

        {/* 3D Card Container */}
        <div className="flex-1 w-full flex relative perspective-1000 items-center justify-center p-6">
          <AnimatePresence initial={false} custom={direction} mode="wait">
            <motion.div
              key={currentIndex}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ x: { type: "spring", stiffness: 300, damping: 30 }, opacity: { duration: 0.2 } }}
              className="w-full h-full relative cursor-pointer group"
              onClick={flipCard}
              style={{ transformStyle: "preserve-3d" }}
            >
              <motion.div
                className="w-full h-full absolute inset-0 rounded-xl"
                animate={{ rotateX: isFlipped ? -180 : 0 }}
                transition={{ duration: 0.5, type: "spring", stiffness: 200, damping: 20 }}
                style={{ transformStyle: "preserve-3d" }}
              >
                {/* Front side - Question */}
                <div
                  className="absolute inset-0 w-full h-full rounded-xl flex border shadow-xl flex-col items-center justify-center p-6 backface-hidden"
                  style={{
                    background: "rgba(151,168,122,0.12)",
                    borderColor: "rgba(151,168,122,0.3)",
                  }}
                >
                  <span className="absolute top-4 left-4 font-data text-[10px] uppercase tracking-wider text-[#97A87A] font-bold">
                    Question
                  </span>
                  <p className="font-brand text-center text-[15px] text-[#dad7cd] font-medium leading-relaxed">
                    {currentCard.question}
                  </p>
                  <p className="absolute bottom-4 font-data text-[10px] text-[#6B7265] group-hover:text-[#97A87A] transition-colors flex items-center gap-1">
                    <RotateCcw size={10} /> Click to flip
                  </p>
                </div>

                {/* Back side - Answer */}
                <div
                  className="absolute inset-0 w-full h-full rounded-xl flex border shadow-xl flex-col items-center justify-center p-6 backface-hidden"
                  style={{
                    background: "rgba(212,168,83,0.1)",
                    borderColor: "rgba(212,168,83,0.3)",
                    transform: "rotateX(180deg)",
                  }}
                >
                  <span className="absolute top-4 left-4 font-data text-[10px] uppercase tracking-wider text-[#D4A853] font-bold">
                    Answer
                  </span>
                  <p className="font-data text-center text-sm text-[#dad7cd] leading-relaxed overflow-y-auto w-full custom-scroll pr-1 pl-1">
                    {currentCard.answer}
                  </p>
                </div>
              </motion.div>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Footer controls */}
        <div className="w-full h-[60px] flex items-center justify-between px-6 border-t border-[#30362A]/30 pb-1">
          <button
            onClick={handlePrev}
            disabled={currentIndex === 0}
            className={`p-2 rounded-lg flex items-center gap-1 transition-all ${
              currentIndex === 0
                ? "opacity-30 cursor-not-allowed text-[#6B7265]"
                : "hover:bg-white/5 cursor-pointer text-[#97A87A]"
            }`}
          >
            <ChevronLeft size={16} />
            <span className="font-data text-xs font-medium">Prev</span>
          </button>
          
          <div className="font-data text-xs text-[#6B7265]">
            <strong className="text-[#dad7cd]">{currentIndex + 1}</strong> / {flashcards.length}
          </div>

          <button
            onClick={handleNext}
            disabled={currentIndex === flashcards.length - 1}
            className={`p-2 rounded-lg flex items-center gap-1 transition-all ${
              currentIndex === flashcards.length - 1
                ? "opacity-30 cursor-not-allowed text-[#6B7265]"
                : "hover:bg-white/5 cursor-pointer text-[#97A87A]"
            }`}
          >
            <span className="font-data text-xs font-medium">Next</span>
            <ChevronRight size={16} />
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
