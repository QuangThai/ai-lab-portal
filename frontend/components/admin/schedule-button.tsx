"use client";

import { useCallback, useState } from "react";
import { CalendarDays, Check, Sparkles, Loader2, X } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";

type SchedulingSuggestion = {
  id: string;
  blog_post_id: string;
  suggested_date: string;
  suggested_time: string;
  rationale: string;
  confidence: number;
  created_at: string;
};

type Props = {
  ideaId: string;
  scheduledAt: string | null | undefined;
};

export function ScheduleButton({ ideaId, scheduledAt }: Props) {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [showPicker, setShowPicker] = useState(false);
  const [suggestion, setSuggestion] = useState<SchedulingSuggestion | null>(null);
  const [loadingSuggestion, setLoadingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  const schedule = useCallback(
    async (dateStr: string) => {
      setSaving(true);
      setSuggestionError(null);
      try {
        const res = await fetch(`/api/admin/blog-ideas/${ideaId}/schedule`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            scheduled_at: dateStr ? new Date(dateStr).toISOString() : null,
          }),
        });
        if (!res.ok) throw new Error("Failed to save");
        router.refresh();
      } catch (err) {
        setSuggestionError(err instanceof Error ? err.message : "Save failed");
      } finally {
        setSaving(false);
        setShowPicker(false);
        setSuggestion(null);
      }
    },
    [ideaId, router],
  );

  const fetchSuggestion = useCallback(async () => {
    setLoadingSuggestion(true);
    setSuggestionError(null);
    try {
      const res = await fetch(`/api/admin/blog-ideas/${ideaId}/suggest-schedule`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: SchedulingSuggestion = await res.json();
      setSuggestion(data);
    } catch (err) {
      setSuggestionError(err instanceof Error ? err.message : "Failed to get suggestion");
    } finally {
      setLoadingSuggestion(false);
    }
  }, [ideaId]);

  const acceptSuggestion = useCallback(() => {
    if (!suggestion) return;
    const combined = `${suggestion.suggested_date}T${suggestion.suggested_time}`;
    schedule(combined);
  }, [suggestion, schedule]);

  const dismissSuggestion = useCallback(() => {
    setSuggestion(null);
  }, []);

  const clearSchedule = useCallback(async () => {
    setSaving(true);
    try {
      const res = await fetch(`/api/admin/blog-ideas/${ideaId}/schedule`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scheduled_at: null }),
      });
      if (!res.ok) throw new Error("Failed to clear");
      router.refresh();
    } catch (err) {
      setSuggestionError(err instanceof Error ? err.message : "Clear failed");
    } finally {
      setSaving(false);
      setSuggestion(null);
    }
  }, [ideaId, router]);

  return (
    <div className="flex flex-col gap-2">
      {/* Error state */}
      {suggestionError && (
        <p className="text-xs text-red-500">{suggestionError}</p>
      )}

      {/* AI Suggestion card */}
      {suggestion && (
        <div className="rounded-lg border border-brand/20 bg-brand/[0.03] p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-xs font-semibold text-brand">
              <Sparkles className="h-3 w-3" />
              AI Suggestion
            </span>
            <button
              type="button"
              onClick={dismissSuggestion}
              className="text-muted-foreground hover:text-foreground"
              aria-label="Dismiss suggestion"
            >
              <X className="h-3 w-3" />
            </button>
          </div>

          <p className="mb-1.5 text-sm font-medium">
            {suggestion.suggested_date} at {suggestion.suggested_time} UTC
          </p>

          <p className="mb-2 text-xs text-muted-foreground leading-relaxed">
            {suggestion.rationale}
          </p>

          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              Confidence: {Math.round(suggestion.confidence * 100)}%
            </span>
            <button
              type="button"
              onClick={acceptSuggestion}
              disabled={saving}
              className="inline-flex items-center gap-1 rounded-lg bg-brand px-2.5 py-1 text-xs font-medium text-white hover:bg-brand/90 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Check className="h-3 w-3" />
              )}
              Accept & Schedule
            </button>
          </div>
        </div>
      )}

      {/* Main button row */}
      <div className="flex items-center gap-1.5">
        {/* Get AI Suggestion (only when no suggestion shown yet) */}
        {!suggestion && (
          <Button
            variant="outline"
            size="sm"
            onClick={fetchSuggestion}
            disabled={loadingSuggestion}
            title="Get AI-powered scheduling suggestion"
          >
            {loadingSuggestion ? (
              <Loader2 className="size-3 animate-spin mr-1" />
            ) : (
              <Sparkles className="size-3 mr-1" />
            )}
            Suggest
          </Button>
        )}

        {/* Manual picker toggle */}
        {showPicker ? (
          <>
            <input
              type="datetime-local"
              className="rounded-md border border-border/60 bg-background px-2 py-1.5 text-xs"
              defaultValue={
                scheduledAt
                  ? new Date(scheduledAt).toISOString().slice(0, 16)
                  : ""
              }
              min={typeof window !== "undefined" ? new Date().toISOString().slice(0, 16) : ""}
              onChange={(e) => schedule(e.target.value)}
            />
            <Button variant="ghost" size="sm" onClick={() => setShowPicker(false)}>
              Cancel
            </Button>
          </>
        ) : (
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowPicker(true)}
              disabled={saving}
            >
              {saving ? (
                <Loader2 className="size-3 animate-spin mr-1" />
              ) : (
                <CalendarDays className="size-3 mr-1" />
              )}
              {scheduledAt ? "Reschedule" : "Pick date"}
            </Button>
            {scheduledAt && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearSchedule}
                disabled={saving}
                className="text-muted-foreground hover:text-red-500"
              >
                <X className="size-3" />
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
