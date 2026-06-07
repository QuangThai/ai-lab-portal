import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { estimateReadingTime, formatReadingTime } from "./reading-time";

describe("estimateReadingTime", () => {
  it("returns 0 for empty input", () => {
    assert.equal(estimateReadingTime(""), 0);
  });

  it("returns 0 for whitespace-only input", () => {
    assert.equal(estimateReadingTime("   \n  \t  "), 0);
  });

  it("returns 1 for very short content (under 200 words)", () => {
    assert.equal(estimateReadingTime("Hello world"), 1);
  });

  it("strips markdown syntax before counting", () => {
    // The plain text has ~50 words
    const content =
      "# Header\n\n" +
      "This is **bold** and *italic* text. Here is a [link](https://example.com). " +
      "![image](https://example.com/img.png) " +
      "> A blockquote here for context.\n\n" +
      "- List item one\n" +
      "- List item two\n" +
      "- List item three\n\n" +
      "1. Ordered item\n" +
      "2. Ordered item\n\n" +
      "Final paragraph with `inline code` to wrap up.";
    const result = estimateReadingTime(content);
    // ~60 words → ceil(60/200) = 1
    assert.equal(result, 1);
  });

  it("strips code blocks entirely", () => {
    const content =
      "Intro paragraph.\n\n```python\ndef hello():\n    print('world')\n```\n\nConclusion.";
    const result = estimateReadingTime(content);
    // "Intro paragraph. Conclusion." = 4 words → ceil(4/200) = 1
    assert.equal(result, 1);
  });

  it("counts 200+ words as 2 minutes", () => {
    const words = Array.from({ length: 250 }, (_, i) => `word${i}`).join(" ");
    assert.equal(estimateReadingTime(words), 2);
  });

  it("counts 400+ words as 3 minutes", () => {
    const words = Array.from({ length: 450 }, (_, i) => `word${i}`).join(" ");
    assert.equal(estimateReadingTime(words), 3);
  });

  it("handles content with only HTML tags (no text)", () => {
    assert.equal(estimateReadingTime("<div><p></p></div>"), 0);
  });

  it("handles content with only markdown syntax", () => {
    assert.equal(estimateReadingTime("***\n# \n> \n- \n"), 1);
  });
});

describe("formatReadingTime", () => {
  it("formats singular", () => {
    assert.equal(formatReadingTime(1), "1 min read");
  });

  it("formats plural", () => {
    assert.equal(formatReadingTime(5), "5 min read");
  });

  it("formats zero", () => {
    assert.equal(formatReadingTime(0), "0 min read");
  });
});
