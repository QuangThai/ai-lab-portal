"""Generate admin boundary headers and test the blog pipeline."""
import json, hmac, hashlib, urllib.request, urllib.error
from time import time

secret = "ai-lab-dev-boundary-2026-secret!"
BASE = "http://127.0.0.1:18000"

def admin_headers():
    payload_str = json.dumps({
        "user_id": "admin-test",
        "email": "admin@example.com",
        "role": "admin",
        "issued_at": int(time()),
    })
    signature = hmac.new(
        secret.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "x-ai-lab-admin-identity": payload_str,
        "x-ai-lab-admin-signature": signature,
        "Content-Type": "application/json",
    }

H = admin_headers()

print("1. Generate idea...", flush=True)
resp = urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/admin/blog-ideas/generate",
    data=json.dumps({"project_name": "AI Lab Portal", "project_summary": "A web portal showcasing AI projects, blog posts about LLMs and code generation"}).encode(),
    headers=H, method="POST",
))
idea = json.loads(resp.read())
idea_id = idea["id"]
print(f"   {idea['title']} ({idea_id})", flush=True)

print("2. Approve idea...", flush=True)
urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/admin/blog-ideas/{idea_id}",
    data=json.dumps({"status": "approved"}).encode(),
    headers=H, method="PATCH",
))

print("3. Generate outline...", flush=True)
resp3 = urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/admin/blog-ideas/{idea_id}/generate-outline",
    data=json.dumps({}).encode(),
    headers=H, method="POST",
))
outline = json.loads(resp3.read())
print(f"   {len(outline.get('outline_sections', []))} sections", flush=True)

print("4. Approve outline...", flush=True)
urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/admin/blog-ideas/{idea_id}",
    data=json.dumps({"outline_status": "approved"}).encode(),
    headers=H, method="PATCH",
))

print("5. Generate draft...", flush=True)
resp5 = urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/admin/blog-ideas/{idea_id}/generate-draft",
    data=json.dumps({}).encode(),
    headers=H, method="POST",
))
draft = json.loads(resp5.read())
md = draft.get("draft_markdown", "")
print(f"   {len(md)} chars", flush=True)
print(f"   Preview: {md[:200]}...", flush=True)

print("6. Approve draft...", flush=True)
urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/admin/blog-ideas/{idea_id}",
    data=json.dumps({"draft_status": "approved"}).encode(),
    headers=H, method="PATCH",
))

print("7. Technical review...", flush=True)
resp7 = urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/admin/blog-ideas/{idea_id}/review-technical",
    data=json.dumps({}).encode(),
    headers=H, method="POST",
))
review = json.loads(resp7.read())
tr = review.get("technical_review", {})
issues = tr.get("issues", [])
print(f"   Risk: {tr.get('overall_risk', '?')}, Issues: {len(issues)}", flush=True)
for i, issue in enumerate(issues[:3]):
    print(f"   [{issue['severity']}] {issue['type']}: {issue['reason'][:80]}", flush=True)

print("", flush=True)
print("=== PIPELINE COMPLETE ===", flush=True)
print(f"Admin UI: http://127.0.0.1:13000/admin/blog-ideas/{idea_id}", flush=True)
