"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowUpRight, BookOpen, Briefcase, FlaskConical } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  publicEntryExcerptClass,
  publicEntryTitleClass,
  publicEyebrowClass,
  publicLandingSectionGap,
  publicSectionHeaderBlockClass,
  publicSectionIntroGapClass,
  publicSectionTitleClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type Entry = {
  description: string;
  href: string;
  icon: LucideIcon;
  index: string;
  span?: "featured" | "default";
  title: string;
};

const entries: Entry[] = [
  {
    index: "01",
    title: "AI Lab",
    description: "Overview of human-reviewed engineering, featured showcases, and latest articles.",
    href: "/lab",
    icon: FlaskConical,
    span: "featured",
  },
  {
    index: "02",
    title: "Showcases",
    description: "Client-ready delivery stories with industry context and publish controls.",
    href: "/showcases",
    icon: Briefcase,
  },
  {
    index: "03",
    title: "Blog",
    description: "Practical AI engineering notes approved before they go public.",
    href: "/blog",
    icon: BookOpen,
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] as const },
  }),
};

function EntryCard({ entry }: { entry: Entry }) {
  const Icon = entry.icon;
  const featured = entry.span === "featured";

  return (
    <Link
      className={cn(
        "group relative flex h-full min-h-60 flex-col justify-between overflow-hidden rounded-[1.75rem] border border-border/80 bg-card/95 p-8 shadow-[0_20px_50px_color-mix(in_srgb,var(--primary)_5%,transparent)] transition-[transform,box-shadow,border-color] duration-300 hover:-translate-y-1 hover:border-brand/30 hover:shadow-[0_28px_60px_color-mix(in_srgb,var(--brand)_12%,transparent)] sm:min-h-[16rem] sm:p-10 lg:p-12",
        featured && "lg:min-h-88"
      )}
      href={entry.href}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-brand/5 blur-2xl transition-opacity duration-300 group-hover:bg-brand/10"
      />
      <div className="relative flex flex-1 flex-col">
        <div className="flex items-start justify-between gap-6">
          <span className="font-(family-name:--font-gt-super) text-4xl leading-none text-brand/75 sm:text-5xl">
            {entry.index}
          </span>
          <span className="flex size-12 items-center justify-center rounded-2xl border border-border/80 bg-muted/50 text-muted-foreground transition-[background-color,color,border-color] duration-300 group-hover:border-brand/25 group-hover:bg-accent group-hover:text-brand">
            <Icon className="size-5" aria-hidden />
          </span>
        </div>
        <h3 className={cn(publicEntryTitleClass, "mt-8 sm:mt-10", featured && "sm:text-4xl")}>{entry.title}</h3>
        <p className={cn(publicEntryExcerptClass, "mt-4 sm:mt-5", featured && "text-base sm:text-lg")}>
          {entry.description.trim()}
        </p>
      </div>
      <span className="relative mt-10 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground transition-colors group-hover:text-brand sm:mt-12">
        Open
        <ArrowUpRight className="size-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" aria-hidden />
      </span>
    </Link>
  );
}

export function PublicHomeEntries() {
  const reduceMotion = useReducedMotion();
  const featured = entries.find((e) => e.span === "featured")!;
  const rest = entries.filter((e) => e.span !== "featured");

  return (
    <section className={publicLandingSectionGap} aria-labelledby="explore-heading">
      <div className={publicSectionHeaderBlockClass}>
        <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between lg:gap-16">
          <div className="max-w-xl">
            <p className={publicEyebrowClass}>Explore</p>
            <h2 id="explore-heading" className={cn(publicSectionTitleClass, publicSectionIntroGapClass)}>
              Start here
            </h2>
          </div>
          <p className="max-w-sm text-base leading-7 text-muted-foreground lg:pb-1 lg:text-right">
            Three public surfaces. One editorial standard for everything that ships.
          </p>
        </div>
      </div>

      <div className="grid gap-6 sm:gap-8 lg:grid-cols-2 lg:gap-10">
        <motion.div custom={0} initial={reduceMotion ? false : "hidden"} animate="show" variants={fadeUp}>
          <EntryCard entry={featured} />
        </motion.div>
        <div className="grid gap-6 sm:gap-8 lg:grid-cols-1 lg:gap-10">
          {rest.map((entry, i) => (
            <motion.div
              key={entry.href}
              custom={i + 1}
              initial={reduceMotion ? false : "hidden"}
              animate="show"
              variants={fadeUp}
            >
              <EntryCard entry={entry} />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
