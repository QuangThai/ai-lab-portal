import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { twScale8 } from "./tailwind-scale";

describe("twScale8", () => {
  it("provides correct height class for spacing-8", () => {
    assert.equal(twScale8.h, "h-[calc(var(--spacing)*8)]");
  });

  it("provides correct size class for spacing-8", () => {
    assert.equal(twScale8.size, "size-[calc(var(--spacing)*8)]");
  });

  it("provides correct min-width class for spacing-8", () => {
    assert.equal(twScale8.minW, "min-w-[calc(var(--spacing)*8)]");
  });

  it("returns same object reference", () => {
    // as const compiles to a plain object in CJS; verify the values are stable
    assert.equal(twScale8.h, "h-[calc(var(--spacing)*8)]");
    assert.equal(twScale8.size, "size-[calc(var(--spacing)*8)]");
    assert.equal(twScale8.minW, "min-w-[calc(var(--spacing)*8)]");
  });
});
