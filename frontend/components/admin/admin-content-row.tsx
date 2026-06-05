"use client";

import type { ReactNode } from "react";
import { motion, type Variants } from "framer-motion";

import { adminListRowClass } from "@/components/admin/admin-ui";
import { cn } from "@/lib/utils";

const rowMotion: Variants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] as const } },
};

type AdminContentRowProps = {
  actions?: ReactNode;
  children: ReactNode;
  meta?: ReactNode;
  title: ReactNode;
};

export function AdminContentRow({ actions, children, meta, title }: AdminContentRowProps) {
  return (
    <motion.li variants={rowMotion} layout className={cn(adminListRowClass, "group")}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0 flex-1 space-y-2.5">
          {meta}
          <div>{title}</div>
          {children}
        </div>
        {actions && (
          <div className="shrink-0 opacity-60 transition-opacity duration-200 group-hover:opacity-100 lg:opacity-40">
            {actions}
          </div>
        )}
      </div>
    </motion.li>
  );
}

export const adminListMotion = {
  container: {
    hidden: {},
    show: { transition: { staggerChildren: 0.05 } },
  },
};
