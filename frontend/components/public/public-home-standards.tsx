"use client";

import { motion, useReducedMotion } from "framer-motion";

import { publicEyebrowClass, publicLandingSectionGap, publicPanelPaddingClass } from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

const standards = [
  "Draft in the CMS",
  "Human review gate",
  "Publish when ready",
  "Public by choice",
] as const;

const fadeIn = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const } },
};

export function PublicHomeStandards() {
  const reduceMotion = useReducedMotion();

  return (
    <motion.section
      className={cn(
        publicLandingSectionGap,
        "rounded-[1.75rem] border border-border/70 bg-muted/30",
        publicPanelPaddingClass
      )}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={fadeIn}
      aria-label="Editorial standards"
    >
      <p className={cn(publicEyebrowClass, "text-center")}>Editorial standard</p>
      <ul className="mt-10 flex flex-col items-center justify-center gap-6 sm:mt-12 sm:flex-row sm:flex-wrap sm:gap-x-12 sm:gap-y-8 lg:gap-x-16">
        {standards.map((item, index) => (
          <li key={item} className="flex items-center gap-4 sm:gap-5">
            <span
              className="font-(family-name:--font-gt-super) text-lg text-brand/70 tabular-nums"
              aria-hidden
            >
              {String(index + 1).padStart(2, "0")}
            </span>
            <span className="text-sm font-semibold uppercase tracking-[0.2em] text-foreground sm:text-base">
              {item}
            </span>
          </li>
        ))}
      </ul>
    </motion.section>
  );
}
