"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import type { ReactNode } from "react";

import { publicFadeUp, publicStaggerContainer, publicStaggerItem } from "@/components/public/public-motion";
import {
  publicEntryExcerptClass,
  publicEntryTitleClass,
  publicEyebrowClass,
  publicListPanelClass,
  publicListRowClass,
  publicMetaClass,
  publicSectionTitleClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type PublicLabSectionItem = {
  excerpt: string;
  href: string;
  meta: ReactNode;
  title: string;
};

type PublicLabSectionProps = {
  index: string;
  items: PublicLabSectionItem[];
  moreHref: string;
  moreLabel: string;
  title: string;
  sectionIndex?: number;
};

export function PublicLabSection({
  index,
  items,
  moreHref,
  moreLabel,
  title,
  sectionIndex = 0,
}: PublicLabSectionProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.section
      className="grid gap-8 sm:grid-cols-[4.5rem_minmax(0,1fr)] sm:gap-10"
      custom={sectionIndex + 1}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={publicFadeUp}
    >
      <p className={cn(publicEyebrowClass, "pt-1 text-2xl tracking-[0.2em] sm:text-3xl")}>{index}</p>
      <div>
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border/80 pb-5 sm:pb-6">
          <h2 className={publicSectionTitleClass}>{title}</h2>
          <Link
            className="inline-flex items-center gap-1.5 text-sm font-semibold uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:text-brand"
            href={moreHref}
          >
            {moreLabel}
            <ArrowUpRight className="size-3.5" aria-hidden />
          </Link>
        </div>
        <motion.div
          className={cn(publicListPanelClass, "mt-6 sm:mt-8")}
          initial={reduceMotion ? false : "hidden"}
          animate="show"
          variants={publicStaggerContainer}
        >
          {items.map((item) => (
            <motion.article key={item.href} variants={reduceMotion ? undefined : publicStaggerItem}>
              <Link className={cn(publicListRowClass, "group")} href={item.href}>
                <div className="flex items-start justify-between gap-6">
                  <div className="min-w-0 flex-1">
                    <p className={publicMetaClass}>{item.meta}</p>
                    <h3 className={cn(publicEntryTitleClass, "mt-2.5 text-xl sm:text-2xl")}>{item.title}</h3>
                    <p className={publicEntryExcerptClass}>{item.excerpt}</p>
                  </div>
                  <span
                    className="mt-1 flex size-9 shrink-0 items-center justify-center rounded-full border border-border/90 text-muted-foreground transition-[border-color,background-color,transform,color] duration-300 group-hover:border-brand/35 group-hover:bg-accent group-hover:text-brand group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                    aria-hidden
                  >
                    <ArrowUpRight className="size-3.5" />
                  </span>
                </div>
              </Link>
            </motion.article>
          ))}
        </motion.div>
      </div>
    </motion.section>
  );
}
