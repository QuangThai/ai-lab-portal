"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { publicFadeUp } from "@/components/public/public-motion";
import {
  publicArticleTitleClass,
  publicEyebrowClass,
  publicMetaClass,
  publicProseMeasureClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type PublicArticleHeaderProps = {
  dateLabel: string;
  eyebrow: ReactNode;
  excerpt: string;
  title: string;
};

export function PublicArticleHeader({ dateLabel, eyebrow, excerpt, title }: PublicArticleHeaderProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.header
      className="relative border-b border-border/80 pb-12 sm:pb-14"
      custom={1}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={publicFadeUp}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -left-4 top-0 hidden h-full w-px bg-linear-to-b from-brand/60 via-brand/20 to-transparent sm:block"
      />
      <p className={publicEyebrowClass}>{eyebrow}</p>
      <p className={cn(publicMetaClass, "mt-4")}>{dateLabel}</p>
      <h1 className={cn(publicArticleTitleClass, "mt-5 sm:mt-6")}>{title}</h1>
      <p className={cn(publicProseMeasureClass, "mt-8 text-xl text-muted-foreground sm:mt-10")}>
        {excerpt}
      </p>
    </motion.header>
  );
}
