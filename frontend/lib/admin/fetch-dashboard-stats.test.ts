import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { AdminDashboardStats } from "./fetch-dashboard-stats";

describe("AdminDashboardStats shape", () => {
  it("should represent a valid stats payload with zero values", () => {
    const stats: AdminDashboardStats = {
      blogDrafts: 0,
      blogPublished: 0,
      blogTotal: 0,
      ideasPending: 0,
      ideasApproved: 0,
      ideasTotal: 0,
      showcasesDrafts: 0,
      showcasesPublished: 0,
      showcasesTotal: 0,
      projectsDrafts: 0,
      projectsPublished: 0,
      projectsTotal: 0,
      newsPublished: 0,
      commentsTotal: 0,
      recentActivity: [],
    };

    assert.equal(stats.blogDrafts, 0);
    assert.equal(stats.recentActivity.length, 0);
    assert.equal(Object.keys(stats).length, 15);
  });

  it("should represent a valid stats payload with real values", () => {
    const stats: AdminDashboardStats = {
      blogDrafts: 2,
      blogPublished: 5,
      blogTotal: 7,
      ideasPending: 3,
      ideasApproved: 1,
      ideasTotal: 4,
      showcasesDrafts: 1,
      showcasesPublished: 3,
      showcasesTotal: 4,
      projectsDrafts: 0,
      projectsPublished: 2,
      projectsTotal: 2,
      newsPublished: 10,
      commentsTotal: 25,
      recentActivity: [
        { action: "publish", actorEmail: "admin@test.com", createdAt: "2026-06-01T00:00:00Z" },
      ],
    };

    assert.equal(stats.blogDrafts, 2);
    assert.equal(stats.blogPublished, 5);
    assert.equal(stats.ideasTotal, 4);
    assert.equal(stats.showcasesPublished, 3);
    assert.equal(stats.projectsTotal, 2);
    assert.equal(stats.newsPublished, 10);
    assert.equal(stats.commentsTotal, 25);
    assert.equal(stats.recentActivity.length, 1);
    assert.equal(stats.recentActivity[0].actorEmail, "admin@test.com");
  });
});
