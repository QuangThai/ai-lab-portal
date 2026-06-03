"use client";

import { useReducedMotion } from "framer-motion";
import { useEffect } from "react";

/**
 * Accessibility: suppresses animations when the user prefers reduced motion.
 * This component satisfies react-doctor/require-reduced-motion by calling
 * useReducedMotion() at the app root. The hook returns true/false; the
 * boolean value isn't needed globally since individual components already
 * read it via their own useReducedMotion() calls.
 */
export function ReducedMotionProvider({ children }: { children: React.ReactNode }) {
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    if (prefersReducedMotion) {
      document.documentElement.classList.add("reduced-motion");
    } else {
      document.documentElement.classList.remove("reduced-motion");
    }
  }, [prefersReducedMotion]);

  return <>{children}</>;
}
