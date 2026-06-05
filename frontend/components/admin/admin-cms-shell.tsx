"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { useReducedMotion } from "framer-motion";
import {
  Briefcase,
  ExternalLink,
  FileText,
  LayoutDashboard,
  Lightbulb,
  Link as LinkIcon,
  MessageSquare,
  Moon,
  Newspaper,
  Rss,
  Sun,
} from "lucide-react";
import { useTheme } from "next-themes";

import { BrandMark } from "@/components/brand/brand-mark";
import { cn } from "@/lib/utils";

type NavKey =
  | "dashboard"
  | "blog"
  | "projects"
  | "showcases"
  | "ideas"
  | "news"
  | "news-review"
  | "submitted-links"
  | "blog-comments";

type Props = { children: ReactNode };

/**
 * Derive the active nav key from the current URL path.
 * Editor routes ("/admin/blog/editor", "/admin/projects/editor", etc.)
 * fall through to their parent section ("blog", "projects", etc.).
 */
function useActiveNavKey(): NavKey {
  const pathname = usePathname();

  if (pathname.startsWith("/admin/login")) return "dashboard";
  if (pathname.startsWith("/admin/blog-ideas")) return "ideas";
  if (pathname.startsWith("/admin/blog-comments")) return "blog-comments";
  if (pathname.startsWith("/admin/blog")) return "blog";
  if (pathname.startsWith("/admin/projects")) return "projects";
  if (pathname.startsWith("/admin/showcases")) return "showcases";
  if (pathname.startsWith("/admin/news-review")) return "news-review";
  if (pathname.startsWith("/admin/news-sources")) return "news";
  if (pathname.startsWith("/admin/news")) return "submitted-links";
  return "dashboard";
}

/* ── Grouped navigation ── */

type NavGroup = { label: string; items: Array<{ key: NavKey; href: string; label: string; icon: ReactNode }> };

const navGroups: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { key: "dashboard", href: "/admin", label: "Dashboard", icon: <LayoutDashboard className="size-4" /> },
    ],
  },
  {
    label: "Content",
    items: [
      { key: "blog", href: "/admin/blog", label: "Blog posts", icon: <FileText className="size-4" /> },
      { key: "ideas", href: "/admin/blog-ideas", label: "Ideas", icon: <Lightbulb className="size-4" /> },
      { key: "blog-comments", href: "/admin/blog-comments", label: "Comments", icon: <MessageSquare className="size-4" /> },
    ],
  },
  {
    label: "Projects & Showcases",
    items: [
      { key: "projects", href: "/admin/projects", label: "Projects", icon: <Briefcase className="size-4" /> },
      { key: "showcases", href: "/admin/showcases", label: "Showcases", icon: <Briefcase className="size-4" /> },
    ],
  },
  {
    label: "AI News",
    items: [
      { key: "news-review", href: "/admin/news-review", label: "News review", icon: <Newspaper className="size-4" /> },
      { key: "submitted-links", href: "/admin/news/submitted-links", label: "Submitted links", icon: <LinkIcon className="size-4" /> },
      { key: "news", href: "/admin/news-sources", label: "News sources", icon: <Rss className="size-4" /> },
    ],
  },
];


function ThemeToggle({ compact }: { compact?: boolean }) {
  const { resolvedTheme, setTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      aria-pressed={isDark}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      suppressHydrationWarning
      className={cn(
        compact
          ? "inline-flex h-7 items-center gap-1 rounded-[var(--radius-admin-sm)] border border-border/60 px-2 text-[11px] font-medium text-muted-foreground transition-all duration-200"
          : "inline-flex h-8 items-center gap-1.5 rounded-[var(--radius-admin-sm)] border border-border/60 px-2.5 text-xs font-medium text-muted-foreground transition-all duration-200",
        "hover:border-border hover:bg-muted/40 hover:text-foreground focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
        "active:scale-[0.97]"
      )}
    >
      {isDark ? <Sun className="size-3" aria-hidden /> : <Moon className="size-3" aria-hidden />}
      <span suppressHydrationWarning>{isDark ? "Light" : "Dark"}</span>
    </button>
  );
}

function NavLink({ active, href, icon, label }: { active: boolean; href: string; icon: ReactNode; label: string }) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group relative flex items-center gap-2.5 rounded-[var(--radius-admin-sm)] px-3 py-2 text-sm font-medium transition-all duration-200",
        "focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
        active
          ? "bg-accent/70 text-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.6)]"
          : "text-muted-foreground hover:bg-muted/25 hover:text-foreground"
      )}
    >
      {active && (
        <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-brand" aria-hidden />
      )}
      <span
        className={cn(
          "flex size-4 shrink-0 items-center justify-center transition-colors",
          active && "text-brand"
        )}
      >
        {icon}
      </span>
      <span>{label}</span>
    </Link>
  );
}

export function AdminCmsShell({ children }: Props) {
  const prefersReducedMotion = useReducedMotion();
  const active = useActiveNavKey();

  return (
    <div className="flex min-h-dvh flex-col bg-background lg:flex-row">
      {/* ── Mobile header ── */}
      <div className="flex items-center justify-between border-b border-border/60 bg-card px-4 py-3 shadow-[0_1px_2px_rgba(0,0,0,0.03)] lg:hidden">
        <div className="flex items-center gap-2">
          <BrandMark />
          <p className="text-sm font-semibold text-foreground">AI Lab</p>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link
            className="inline-flex h-8 items-center gap-1 rounded-[var(--radius-admin-sm)] border border-border/60 px-2.5 text-xs font-medium text-muted-foreground transition-all duration-200 hover:border-border hover:bg-muted/40 hover:text-foreground active:scale-[0.97]"
            href="/"
            target="_blank"
            rel="noopener noreferrer"
          >
            Site
            <ExternalLink className="size-3" aria-hidden />
          </Link>
        </div>
      </div>

      {/* ── Desktop sidebar ── */}
      <aside className="hidden w-56 shrink-0 flex-col border-r border-border/60 bg-card shadow-[1px_0_3px_rgba(0,0,0,0.03)] lg:sticky lg:top-0 lg:flex lg:h-dvh lg:self-start">
        {/* Brand header */}
        <Link
          href="/"
          className="group flex items-center gap-2 border-b border-border/60 px-4 py-4 transition-colors hover:bg-muted/10"
        >
          <BrandMark />
          <p className="text-sm font-semibold text-foreground">AI Lab</p>
        </Link>

        {/* Navigation — grouped by section */}
        <nav aria-label="Admin navigation" className="flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto p-3">
          {navGroups.map((group) => (
            <div key={group.label} className="flex flex-col">
              <span className="px-3 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/60 select-none">
                {group.label}
              </span>
              {group.items.map((item) => (
                <NavLink key={item.key} active={active === item.key} href={item.href} icon={item.icon} label={item.label} />
              ))}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="flex items-center justify-between gap-1 border-t border-border/60 px-2.5 py-2">
          <Link
            className="inline-flex h-7 items-center gap-1 rounded-[var(--radius-admin-sm)] px-2 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted/25 hover:text-foreground"
            href="/"
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="size-3" aria-hidden />
            Site
          </Link>
          <ThemeToggle compact />
        </div>
      </aside>

      {/* ── Main content ── */}
      <main
        className={cn(
          "min-w-0 flex-1 px-5 py-6 sm:px-7 sm:py-8",
          !prefersReducedMotion && "animate-in fade-in duration-200"
        )}
      >
        {children}
      </main>
    </div>
  );
}
