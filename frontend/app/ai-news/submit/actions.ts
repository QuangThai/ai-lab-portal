"use server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export type SubmitLinkState = {
  ok: boolean;
  message: string;
};

export async function submitAiNewsLinkAction(
  _prev: SubmitLinkState | null,
  formData: FormData,
): Promise<SubmitLinkState> {
  const url = String(formData.get("url") ?? "").trim();
  if (!url) {
    return { ok: false, message: "URL is required." };
  }

  const response = await fetch(`${backendBaseUrl}/public/submitted-links`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url,
      submitter_name: String(formData.get("name") ?? "").trim() || null,
      submitter_email: String(formData.get("email") ?? "").trim() || null,
      note: String(formData.get("note") ?? "").trim() || null,
      suggested_category: String(formData.get("category") ?? "").trim() || null,
    }),
  });

  const body = (await response.json().catch(() => ({}))) as { detail?: string; message?: string };

  if (response.status === 429) {
    return { ok: false, message: body.detail ?? "Too many submissions. Try again later." };
  }

  if (!response.ok) {
    return { ok: false, message: body.detail ?? `Submission failed (${response.status}).` };
  }

  return {
    ok: true,
    message: body.message ?? "Link submitted for review.",
  };
}
