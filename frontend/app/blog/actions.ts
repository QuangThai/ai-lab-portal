"use server";

import { headers } from "next/headers";
import { revalidatePath } from "next/cache";

import { auth } from "@/lib/auth/server";
import {
  toggleReaction as apiToggleReaction,
  toggleBookmark as apiToggleBookmark,
  createComment as apiCreateComment,
} from "@/lib/blog/social";

export async function toggleReactionAction(slug: string, emoji: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Not authenticated");

  await apiToggleReaction(slug, emoji, session);
  revalidatePath(`/blog/${slug}`);
}

export async function toggleBookmarkAction(slug: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Not authenticated");

  await apiToggleBookmark(slug, session);
  revalidatePath(`/blog/${slug}`);
}

export async function createCommentAction(
  slug: string,
  content: string,
  parentId: string | undefined,
) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Not authenticated");

  await apiCreateComment(slug, content, parentId, session);
  revalidatePath(`/blog/${slug}`);
}
