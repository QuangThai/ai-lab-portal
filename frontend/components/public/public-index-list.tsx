"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { publicFadeUp, publicStaggerContainer } from "@/components/public/public-motion";
import { PublicEmptyState } from "@/components/public/public-empty-state";
import { publicListPanelClass } from "@/components/public/public-ui";

type PublicIndexListProps = {
  children: ReactNode;
  emptyDescription: string;
  emptyTitle: string;
  isEmpty: boolean;
};

export function PublicIndexList({ children, emptyDescription, emptyTitle, isEmpty }: PublicIndexListProps) {
  const reduceMotion = useReducedMotion();

  if (isEmpty) {
    return (
      <motion.div
        initial={reduceMotion ? false : "hidden"}
        animate="show"
        custom={1}
        variants={publicFadeUp}
      >
        <PublicEmptyState description={emptyDescription} title={emptyTitle} />
      </motion.div>
    );
  }

  return (
    <motion.div
      className={publicListPanelClass}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={publicStaggerContainer}
    >
      {children}
    </motion.div>
  );
}
