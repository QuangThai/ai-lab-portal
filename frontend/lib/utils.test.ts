import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { cn } from "./utils";

describe("cn", () => {
  it("merges class names", () => {
    assert.equal(cn("a", "b"), "a b");
  });

  it("handles conditional classes", () => {
    assert.equal(cn("base", false && "hidden", "visible"), "base visible");
  });

  it("merges Tailwind conflicts correctly", () => {
    // twMerge should keep the last conflicting class
    const result = cn("px-4", "px-6");
    assert.equal(result, "px-6");
  });

  it("handles undefined and null inputs", () => {
    assert.equal(cn("a", undefined, null, "b"), "a b");
  });

  it("handles object syntax", () => {
    assert.equal(cn({ foo: true, bar: false }), "foo");
  });

  it("returns empty string for no inputs", () => {
    assert.equal(cn(), "");
  });
});
