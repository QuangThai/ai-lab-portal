"use client";

import type { ReactNode } from "react";
import { motion, type Variants } from "framer-motion";

import { adminListRowClass } from "@/components/admin/admin-ui";
import { cn } from "@/lib/utils";

const rowMotion: Variants = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] as const } },
};

type AdminContentRowProps = {
  actions?: ReactNode;
  children: ReactNode;
  meta?: ReactNode;
  title: ReactNode;
};

export function AdminContentRow({ actions, children, meta, title }: AdminContentRowProps) {
  return (
    <motion.li variants={rowMotion} layout className={cn(adminListRowClass)}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0 flex-1 space-y-2.5">
          {meta}
          <div>{title}</div>
          {children}
        </div>
        {actions}
      </div>
    </motion.li>
  );
}

export const adminListMotion = {
  container: {
    hidden: {},
    show: { transition: { staggerChildren: 0.04 } },
  },
};
