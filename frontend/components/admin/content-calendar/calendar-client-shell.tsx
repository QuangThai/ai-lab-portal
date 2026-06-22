"use client";

import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, GripVertical, Search, X, SlidersHorizontal } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { adminPageStackClass } from "@/components/admin/admin-ui";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

/* ── Types ── */

export interface CalendarPost {
  id: string;
  title: string;
  slug?: string;
  type: "post" | "idea";
  status: string;
  date?: string | null;
  stage?: string;
  scheduled_at?: string | null;
  created_at?: string;
}

export interface CalendarData {
  published: CalendarPost[];
  pipeline: CalendarPost[];
  scheduled: CalendarPost[];
  month_counts: Record<string, number>;
}

/* ── Helpers ── */

function getMonthDays(year: number, month: number) {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const days: (number | null)[] = [];
  for (let i = 0; i < firstDay.getDay(); i++) days.push(null);
  for (let d = 1; d <= lastDay.getDate(); d++) days.push(d);
  return days;
}

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const DAY_HEADERS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function heatmapBg(count: number, maxCount: number): string {
  if (count === 0) return "";
  const ratio = count / Math.max(maxCount, 1);
  if (ratio > 0.66) return "bg-emerald-500/15";
  if (ratio > 0.33) return "bg-emerald-500/10";
  return "bg-emerald-500/5";
}

/* ── Stage Badge ── */

function stageBadge(stage: string | undefined) {
  const colors: Record<string, string> = {
    published: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    marketing_done: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
    reviewed: "bg-purple-500/10 text-purple-600 dark:text-purple-400",
    draft_done: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
    outline_done: "bg-brand/10 text-brand",
    approved: "bg-muted text-muted-foreground",
    scheduled: "bg-sky-500/10 text-sky-600 dark:text-sky-400",
    idea: "bg-muted/50 text-muted-foreground",
  };
  const label: Record<string, string> = {
    published: "Published",
    marketing_done: "Marketing",
    reviewed: "Reviewed",
    draft_done: "Draft",
    outline_done: "Outline",
    approved: "Approved",
    scheduled: "Scheduled",
    idea: "Idea",
  };
  return (
    <span
      className={cn(
        "inline-block rounded px-1.5 py-0.5 text-[10px] font-medium",
        colors[stage ?? "idea"] ?? "bg-muted text-muted-foreground",
      )}
    >
      {label[stage ?? "idea"] ?? stage}
    </span>
  );
}

/* ── Calendar Grid (with drop zones) ── */

function CalendarGrid({
  year,
  month,
  postsByDate,
  scheduledByDate,
  dragOverDate,
  onDragOver,
  onDragLeave,
  onDrop,
  onDateClick,
  selectedDate,
}: {
  year: number;
  month: number;
  postsByDate: Map<string, CalendarPost[]>;
  scheduledByDate: Map<string, CalendarPost[]>;
  dragOverDate: string | null;
  onDragOver: (dateStr: string) => void;
  onDragLeave: () => void;
  onDrop: (dateStr: string) => void;
  onDateClick: (dateStr: string | null) => void;
  selectedDate: string | null;
}) {
  const days = getMonthDays(year, month);
  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;

  let maxCount = 0;
  for (const [, posts] of postsByDate) {
    maxCount = Math.max(maxCount, posts.length);
  }

  return (
    <div className="rounded-xl border border-border/60 bg-card overflow-hidden">
      {/* Day headers */}
      <div className="grid grid-cols-7 border-b border-border/60">
        {DAY_HEADERS.map((d) => (
          <div
            key={d}
            className="px-2 py-2 text-center text-[11px] font-semibold text-muted-foreground uppercase tracking-wider border-r border-border/30 last:border-r-0"
          >
            {d}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7">
        {days.map((day, idx) => {
          if (day === null) {
            return <div key={`empty-${idx}`} className="min-h-20 border-r border-b border-border/30 last:border-r-0 bg-muted/20" />;
          }

          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const dayPosts = postsByDate.get(dateStr) ?? [];
          const dayScheduled = scheduledByDate.get(dateStr) ?? [];
          const isToday = dateStr === todayStr;
          const isSelected = dateStr === selectedDate;
          const isDragOver = dateStr === dragOverDate;
          const allItems = [...dayPosts, ...dayScheduled];
          const displayItems = allItems.slice(0, 3);
          const hasMore = allItems.length > 3;

          return (
            <div
              key={dateStr}
              data-calendar-cell={dateStr}
              className={cn(
                "min-h-20 p-1.5 border-r border-b border-border/30 last:border-r-0 cursor-pointer transition-all duration-150",
                heatmapBg(dayPosts.length, maxCount),
                isToday && "ring-1 ring-inset ring-brand/30",
                isSelected && "bg-brand/5",
                isDragOver && "bg-brand/10 ring-2 ring-inset ring-brand/40 scale-[1.02]",
              )}
              onClick={() => onDateClick(isSelected ? null : dateStr)}
              onDragOver={(e) => { e.preventDefault(); onDragOver(dateStr); }}
              onDragLeave={onDragLeave}
              onDrop={(e) => { e.preventDefault(); onDrop(dateStr); }}
              tabIndex={0}
            >
              <span
                className={cn(
                  "inline-flex items-center justify-center w-6 h-6 text-xs font-medium rounded-full",
                  isToday && "bg-brand text-white",
                  !isToday && "text-muted-foreground",
                )}
              >
                {day}
              </span>
              <div className="mt-0.5 space-y-0.5">
                {displayItems.map((item) => (
                  <a
                    key={`${item.type}-${item.id}`}
                    href={
                      item.type === "post" && item.slug
                        ? `/blog/${item.slug}`
                        : `/admin/blog-ideas/${item.id}`
                    }
                    onClick={(e) => e.stopPropagation()}
                    className={cn(
                      "block truncate rounded px-1 py-0.5 text-[10px] leading-tight transition-colors",
                      item.type === "post"
                        ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/20"
                        : item.scheduled_at
                          ? "bg-sky-500/10 text-sky-700 dark:text-sky-300 hover:bg-sky-500/20"
                          : "bg-amber-500/10 text-amber-700 dark:text-amber-300 hover:bg-amber-500/20",
                    )}
                  >
                    {item.title}
                  </a>
                ))}
                {hasMore && (
                  <span className="text-[10px] text-muted-foreground block px-1">
                    +{allItems.length - 3} more
                  </span>
                )}
              </div>

              {/* Popover */}
              {isSelected && allItems.length > 0 && (
                <motion.div
                  className="absolute z-10 left-0 right-0 top-full mt-1 rounded-lg border border-border/60 bg-card shadow-lg p-3 min-w-[200px]"
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.15 }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <p className="text-xs font-semibold mb-2 text-foreground">
                    {MONTHS[month]} {day}, {year}
                  </p>
                  <div className="space-y-1.5">
                    {allItems.slice(0, 8).map((item) => (
                      <a
                        key={`popover-${item.type}-${item.id}`}
                        href={
                          item.type === "post" && item.slug
                            ? `/blog/${item.slug}`
                            : `/admin/blog-ideas/${item.id}`
                        }
                        className="block text-xs leading-tight py-1 px-1.5 rounded hover:bg-muted transition-colors"
                      >
                        <span className="font-medium">{item.title}</span>
                        <span className="text-muted-foreground ml-1.5">
                          {item.type === "post" ? "Published" : item.scheduled_at ? "Scheduled" : "Pipeline"}
                        </span>
                      </a>
                    ))}
                    {allItems.length > 8 && (
                      <p className="text-[10px] text-muted-foreground pt-1">
                        +{allItems.length - 8} more items
                      </p>
                    )}
                  </div>
                </motion.div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Mini Timeline ── */

function MiniTimeline({ scheduled }: { scheduled: CalendarPost[] }) {
  if (scheduled.length === 0) return null;

  const upcoming = scheduled
    .filter((s) => s.scheduled_at)
    .sort((a, b) => (a.scheduled_at ?? "").localeCompare(b.scheduled_at ?? ""));

  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
        <span className="size-1.5 rounded-full bg-sky-500" />
        Upcoming Schedule
      </h3>
      <div className="relative pl-6 space-y-3">
        <div className="absolute left-2.5 top-1 bottom-0 w-px bg-border/60" />
        {upcoming.slice(0, 5).map((item, i) => (
          <motion.div
            key={item.id}
            className="relative"
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05, duration: 0.3 }}
          >
            <span className="absolute -left-[18px] top-1.5 size-3 rounded-full border-2 border-sky-400 bg-card" />
            <a
              href={`/admin/blog-ideas/${item.id}`}
              className="block text-sm hover:text-brand transition-colors"
            >
              <span className="font-medium">{item.title}</span>
              <span className="text-xs text-muted-foreground ml-2">
                {item.scheduled_at
                  ? new Date(item.scheduled_at).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })
                  : ""}
              </span>
            </a>
          </motion.div>
        ))}
        {upcoming.length > 5 && (
          <p className="text-xs text-muted-foreground pl-1">
            +{upcoming.length - 5} more scheduled
          </p>
        )}
      </div>
    </div>
  );
}

/* ── Draggable Idea Card ── */

function DraggableIdeaCard({
  idea,
}: {
  idea: CalendarPost;
}) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData("text/plain", idea.id);
    e.dataTransfer.effectAllowed = "move";
    setIsDragging(true);
  };

  const handleDragEnd = () => {
    setIsDragging(false);
  };

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      className={cn(
        "flex items-center gap-2 rounded-lg border border-border/30 p-2.5 transition-all cursor-grab active:cursor-grabbing",
        isDragging
          ? "opacity-40 scale-95 border-brand/40 shadow-sm"
          : "hover:bg-muted/30 hover:border-border/50",
      )}
    >
      <GripVertical className="size-3.5 shrink-0 text-muted-foreground/40" />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium truncate">{idea.title}</p>
        <p className="text-[10px] text-muted-foreground mt-0.5">{stageBadge(idea.stage)}</p>
      </div>
      <span className="text-[9px] text-muted-foreground shrink-0">Drag to date</span>
    </div>
  );
}

/* ── Client shell ── */



export function CalendarClientShell({
  initialData,
}: {
  initialData: CalendarData;
}) {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());
  const [data, setData] = useState(initialData);
  const [dragOverDate, setDragOverDate] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterStage, setFilterStage] = useState<string>("all");
  const dragOverDateRef = useRef<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const goPrev = useCallback(
    () => setMonth((m) => (m === 0 ? (setYear((y) => y - 1), 11) : m - 1)),
    [setYear],
  );
  const goNext = useCallback(
    () => setMonth((m) => (m === 11 ? (setYear((y) => y + 1), 0) : m + 1)),
    [setYear],
  );
  const goToday = useCallback(() => {
    const n = new Date();
    setYear(n.getFullYear());
    setMonth(n.getMonth());
  }, [setYear, setMonth]);

  // Clear feedback after 3s
  useEffect(() => {
    if (feedback) {
      const t = setTimeout(() => setFeedback(null), 3000);
      return () => clearTimeout(t);
    }
  }, [feedback]);

  // Apply search + filter
  const filteredPipeline = data.pipeline.filter((p) => {
    if (searchQuery && !p.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (filterStatus === "published" || filterStatus === "scheduled") return false;
    if (filterStatus === "pipeline" && p.scheduled_at) return false;
    if (filterStage !== "all" && p.stage !== filterStage) return false;
    return true;
  });

  const filteredPublished = data.published.filter((p) => {
    if (searchQuery && !p.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  // Unscheduled ideas for drag (from filtered pipeline)
  const unscheduledIdeas = filteredPipeline.filter(
    (p) => p.stage && p.stage !== "published" && !p.scheduled_at,
  );

  // Group published posts by date
  const postsByDate = new Map<string, CalendarPost[]>();
  for (const post of filteredPublished) {
    if (post.date) {
      const dateKey = post.date.slice(0, 10);
      const existing = postsByDate.get(dateKey) ?? [];
      existing.push(post);
      postsByDate.set(dateKey, existing);
    }
  }

  // Group scheduled items by date
  const scheduledByDate = new Map<string, CalendarPost[]>();
  for (const item of filteredPipeline) {
    if (item.scheduled_at) {
      const dateKey = item.scheduled_at.slice(0, 10);
      const existing = scheduledByDate.get(dateKey) ?? [];
      existing.push(item);
      scheduledByDate.set(dateKey, existing);
    }
  }

  // Stats
  const publishedCount = filteredPublished.length;
  const inProgress = filteredPipeline.filter(
    (p) => p.stage && p.stage !== "published",
  ).length;
  const ideas = filteredPipeline.length;
  const scheduledCount = data.scheduled.filter((s) =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase()),
  ).length;

  // ── Drag & Drop handlers ──

  // Sync ref with state so global drop handler always has latest value
  useEffect(() => {
    dragOverDateRef.current = dragOverDate;
  }, [dragOverDate]);

  const handleDragOver = useCallback((dateStr: string) => {
    setDragOverDate(dateStr);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOverDate(null);
  }, []);

  const handleSchedule = useCallback(
    async (ideaId: string, dateStr: string) => {
      setDragOverDate(null);
      try {
        const scheduledDate = new Date(dateStr + "T12:00:00");
        const res = await fetch(`/admin/blog-ideas/${ideaId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scheduled_at: scheduledDate.toISOString() }),
        });

        if (!res.ok) {
          setFeedback("Failed to schedule");
          return;
        }

        // Optimistic UI: move idea to scheduled
        setData((prev) => {
          const updatedPipeline = prev.pipeline.map((p) =>
            p.id === ideaId ? { ...p, scheduled_at: scheduledDate.toISOString() } : p,
          );
          return {
            ...prev,
            pipeline: updatedPipeline,
            scheduled: [
              ...prev.scheduled,
              ...updatedPipeline
                .filter((p) => p.id === ideaId)
                .map((s) => ({ ...s, scheduled_at: scheduledDate.toISOString() })),
            ],
          };
        });

        setFeedback(`Scheduled for ${scheduledDate.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        })}`);
      } catch {
        setFeedback("Failed to schedule");
      } finally {
      }
    },
    [],
  );

  // Listen for drops from draggable ideas — uses ref to avoid stale closure
  useEffect(() => {
    const handler = (e: DragEvent) => {
      const ideaId = e.dataTransfer?.getData("text/plain");
      const targetDate = dragOverDateRef.current;
      if (!ideaId || !targetDate) return;

      const target = e.target as HTMLElement;
      if (target.closest && target.closest("[data-calendar-cell]")) {
        handleSchedule(ideaId, targetDate);
      }
    };

    document.addEventListener("drop", handler);
    return () => document.removeEventListener("drop", handler);
  }, [handleSchedule]);

  return (
    <motion.div
      className={cn("space-y-6", adminPageStackClass)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Feedback toast */}
      {feedback && (
        <motion.div
          className="fixed top-4 right-4 z-50 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700 shadow-lg dark:border-emerald-800/30 dark:bg-emerald-950/20 dark:text-emerald-400"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
        >
          {feedback}
        </motion.div>
      )}

      {/* Stat cards */}
      <div className="grid gap-3 sm:grid-cols-4">
        {[
          { label: "Published", value: publishedCount, color: "text-emerald-600 dark:text-emerald-400" },
          { label: "In Pipeline", value: inProgress, color: "text-amber-600 dark:text-amber-400" },
          { label: "Scheduled", value: scheduledCount, color: "text-sky-600 dark:text-sky-400" },
          { label: "Total Ideas", value: ideas, color: "text-foreground" },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            className="rounded-xl border border-border/60 bg-card p-4"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * i, duration: 0.3 }}
          >
            <p className="text-xs font-medium text-muted-foreground mb-1">{stat.label}</p>
            <p className={cn("text-2xl font-bold", stat.color)}>{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Month navigation + filter/search */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">
          {MONTHS[month]} {year}
        </h2>
        <div className="flex items-center gap-2 flex-wrap">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
            <Input
              placeholder="Search posts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8 w-44 pl-8 text-xs"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="size-3" />
              </button>
            )}
          </div>

          {/* Status filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="h-8 rounded-lg border border-border/60 bg-background px-2.5 text-xs font-medium text-muted-foreground"
          >
            <option value="all">All status</option>
            <option value="published">Published</option>
            <option value="pipeline">Pipeline</option>
            <option value="scheduled">Scheduled</option>
          </select>

          {/* Stage filter */}
          <select
            value={filterStage}
            onChange={(e) => setFilterStage(e.target.value)}
            className="h-8 rounded-lg border border-border/60 bg-background px-2.5 text-xs font-medium text-muted-foreground"
          >
            <option value="all">All stages</option>
            <option value="idea">Idea</option>
            <option value="outline_done">Outline</option>
            <option value="draft_done">Draft</option>
            <option value="reviewed">Reviewed</option>
            <option value="marketing_done">Marketing</option>
            <option value="approved">Approved</option>
          </select>

          {/* Toggle sidebar */}
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className={cn(
              "rounded-lg border p-1.5 transition-colors",
              sidebarOpen
                ? "border-brand/40 bg-brand/5 text-brand"
                : "border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted/50",
            )}
          >
            <SlidersHorizontal className="size-4" />
          </button>

          <button
            onClick={goToday}
            className="rounded-lg border border-border/60 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          >
            Today
          </button>
          <button
            onClick={goPrev}
            className="rounded-lg border border-border/60 p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          >
            <ChevronLeft className="size-4" />
          </button>
          <button
            onClick={goNext}
            className="rounded-lg border border-border/60 p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          >
            <ChevronRight className="size-4" />
          </button>
        </div>
      </div>

      {/* Unscheduled ideas — drag source */}
      {unscheduledIdeas.length > 0 && (
        <motion.div
          className="rounded-xl border-2 border-dashed border-brand/20 bg-brand/[0.02] p-4"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center gap-2 mb-3">
            <GripVertical className="size-4 text-brand" />
            <h3 className="text-sm font-semibold text-foreground">
              Drag & Drop Scheduling
            </h3>
            <span className="text-[10px] text-muted-foreground">
              Drag ideas onto calendar dates to schedule
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {unscheduledIdeas.slice(0, 8).map((idea) => (
              <DraggableIdeaCard
                key={idea.id}
                idea={idea}
              />
            ))}
            {unscheduledIdeas.length > 8 && (
              <span className="text-xs text-muted-foreground self-center">
                +{unscheduledIdeas.length - 8} more
              </span>
            )}
          </div>
        </motion.div>
      )}

      {/* Main content + optional sidebar */}
      <div className={cn("flex gap-6", sidebarOpen ? "flex-col lg:flex-row" : "")}>
        {/* Calendar grid area */}
        <div className={cn("flex-1 min-w-0", sidebarOpen ? "" : "")}>
          <motion.div
            key={`${year}-${month}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <CalendarGrid
              year={year}
              month={month}
              postsByDate={postsByDate}
              scheduledByDate={scheduledByDate}
              dragOverDate={dragOverDate}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              // eslint-disable-next-line @typescript-eslint/no-unused-vars
              onDrop={(_dateStr: string) => {
                // Handled globally via document-level drop listener
              }}
              onDateClick={(d) => setSelectedDate(d)}
              selectedDate={selectedDate}
            />
          </motion.div>

          <div className="grid gap-6 mt-6 lg:grid-cols-1">
            <MiniTimeline scheduled={data.scheduled} />
          </div>
        </div>

        {/* Stats sidebar */}
        {sidebarOpen && (
          <motion.aside
            className="w-full lg:w-72 shrink-0 space-y-4"
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25 }}
          >
            {/* Pipeline breakdown */}
            <div className="rounded-xl border border-border/60 bg-card p-4">
              <h3 className="text-sm font-semibold mb-3">Pipeline Breakdown</h3>
              <div className="space-y-2">
                {[
                  { label: "Ideas", count: filteredPipeline.filter((p) => p.stage === "idea" || !p.stage).length, color: "bg-muted" },
                  { label: "Outline", count: filteredPipeline.filter((p) => p.stage === "outline_done").length, color: "bg-brand/30" },
                  { label: "Draft", count: filteredPipeline.filter((p) => p.stage === "draft_done").length, color: "bg-amber-500/30" },
                  { label: "Review", count: filteredPipeline.filter((p) => p.stage === "reviewed").length, color: "bg-purple-500/30" },
                  { label: "Marketing", count: filteredPipeline.filter((p) => p.stage === "marketing_done").length, color: "bg-blue-500/30" },
                  { label: "Approved", count: filteredPipeline.filter((p) => p.stage === "approved").length, color: "bg-emerald-500/30" },
                ].map((stage) => (
                  <div key={stage.label} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className={cn("size-2 rounded-full", stage.color)} />
                      <span className="text-muted-foreground">{stage.label}</span>
                    </div>
                    <span className="font-medium">{stage.count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Month stats */}
            <div className="rounded-xl border border-border/60 bg-card p-4">
              <h3 className="text-sm font-semibold mb-3">This Month</h3>
              {(() => {
                const monthStr = `${year}-${String(month + 1).padStart(2, "0")}`;
                const monthPublished = data.published.filter(
                  (p) => p.date && p.date.startsWith(monthStr),
                ).length;
                const monthScheduled = data.pipeline.filter(
                  (p) => p.scheduled_at && p.scheduled_at.startsWith(monthStr),
                ).length;
                return (
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Published</span>
                      <span className="font-medium text-emerald-600 dark:text-emerald-400">{monthPublished}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Scheduled</span>
                      <span className="font-medium text-sky-600 dark:text-sky-400">{monthScheduled}</span>
                    </div>
                    <div className="flex justify-between border-t border-border/30 pt-2 mt-2">
                      <span className="text-muted-foreground">Day with most posts</span>
                      <span className="font-medium">
                        {(() => {
                          let maxDay = "--";
                          let maxCount = 0;
                          for (const [date, posts] of postsByDate) {
                            if (date.startsWith(monthStr) && posts.length > maxCount) {
                              maxCount = posts.length;
                              maxDay = date.slice(8, 10);
                            }
                          }
                          return maxDay !== "--" ? `${maxDay} (${maxCount})` : "--";
                        })()}
                      </span>
                    </div>
                  </div>
                );
              })()}
            </div>
          </motion.aside>
        )}
      </div>
    </motion.div>
  );
}
