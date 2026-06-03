"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowLeft } from "lucide-react";

import { publicFadeIn } from "@/components/public/public-motion";
import { publicBackLinkClass } from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type PublicBackLinkProps = {
  children: string;
  href: string;
};

export function PublicBackLink({ children, href }: PublicBackLinkProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div initial={reduceMotion ? false : "hidden"} animate="show" variants={publicFadeIn}>
      <Link className={cn(publicBackLinkClass, "group")} href={href}>
        <ArrowLeft className="size-3.5 transition-transform duration-200 group-hover:-translate-x-0.5" aria-hidden />
        {children}
      </Link>
    </motion.div>
  );
}
