"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";

import { pollGenerationJobAction } from "./actions";

type Props = {
  ideaId: string;
  taskId?: string;
  opStatus?: string;
};

export function GenerationJobPoller({ ideaId, taskId, opStatus }: Props) {
  const router = useRouter();
  const polling = useRef(false);

  useEffect(() => {
    if (!taskId || opStatus !== "queued" || polling.current) return;
    polling.current = true;

    let cancelled = false;

    const poll = async () => {
      for (let attempt = 0; attempt < 60 && !cancelled; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        const job = await pollGenerationJobAction(taskId);
        if (job.status === "completed") {
          router.refresh();
          return;
        }
        if (job.status === "failed") {
          const params = new URLSearchParams({
            opStage: job.stage,
            opStatus: "error",
            message: job.error_message ?? "Generation failed in the worker.",
          });
          router.replace(`/admin/blog-ideas/${ideaId}?${params.toString()}`);
          return;
        }
      }
    };

    void poll();
    return () => {
      cancelled = true;
    };
  }, [ideaId, taskId, opStatus, router]);

  return null;
}
