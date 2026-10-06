import { describe, expect, it } from "vitest"
import { escapeHtml } from "@/lib/email"
import { isValidEmail } from "@/lib/validation"

describe("escapeHtml", () => {
  it("neutralizes HTML in user input", () => {
    expect(escapeHtml(`<a href="x" onclick='y'>&</a>`)).toBe(
      "&lt;a href=&quot;x&quot; onclick=&#39;y&#39;&gt;&amp;&lt;/a&gt;",
    )
  })

  it("handles null and non-string values", () => {
    expect(escapeHtml(null)).toBe("")
    expect(escapeHtml(42)).toBe("42")
  })
})

describe("isValidEmail", () => {
  it.each(["rider@helmx.com", "a.b+c@sub.example.pk"])("accepts %s", (email) => {
    expect(isValidEmail(email)).toBe(true)
  })

  it.each(["", "no-at-sign", "a@b", "a @b.com", 123, null, `${"a".repeat(250)}@b.com`])("rejects %s", (email) => {
    expect(isValidEmail(email)).toBe(false)
  })
})
