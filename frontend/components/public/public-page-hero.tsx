"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { publicFadeUp } from "@/components/public/public-motion";
import {
  publicEyebrowClass,
  publicLeadClass,
  publicPageHeroPanelClass,
  publicPageTitleClass,
  publicPanelPaddingClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type PublicPageHeroProps = {
  actions?: ReactNode;
  description: string;
  eyebrow: string;
  title: string;
  variant?: "default" | "panel";
};

export function PublicPageHero({
  actions,
  description,
  eyebrow,
  title,
  variant = "default",
}: PublicPageHeroProps) {
  const reduceMotion = useReducedMotion();
  const isPanel = variant === "panel";

  const content = (
    <>
      <div
        aria-hidden
        className={cn(
          "pointer-events-none absolute -right-8 top-0 h-32 w-32 rounded-full bg-brand/8 blur-3xl",
          isPanel ? "opacity-100" : "hidden"
        )}
      />
      <div className="relative min-w-0">
        <p className={publicEyebrowClass}>{eyebrow}</p>
        <h1 className={cn(publicPageTitleClass, "mt-5 sm:mt-6")}>{title}</h1>
        <p className={cn(publicLeadClass, "mt-7 sm:mt-8")}>{description}</p>
      </div>
      {actions ? (
        <div className="relative flex shrink-0 flex-wrap gap-3 lg:mt-2">{actions}</div>
      ) : null}
    </>
  );

  if (isPanel) {
    return (
      <motion.header
        className={cn(
          publicPageHeroPanelClass,
          publicPanelPaddingClass,
          actions && "grid gap-10 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end lg:gap-14 xl:gap-16"
        )}
        custom={0}
        initial={reduceMotion ? false : "hidden"}
        animate="show"
        variants={publicFadeUp}
      >
        {content}
      </motion.header>
    );
  }

  return (
    <motion.header
      className={cn(
        "border-b border-border/80 pb-12 sm:pb-14",
        actions && "grid gap-10 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end lg:gap-12"
      )}
      custom={0}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={publicFadeUp}
    >
      {content}
    </motion.header>
  );
}
