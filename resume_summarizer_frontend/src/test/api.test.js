import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError } from "../api";
import { KEY } from "./fixtures";

afterEach(() => vi.restoreAllMocks());

function mockFetch(status = 200, body = {}) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(status === 204 ? null : JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }),
  );
}

describe("api client", () => {
  it("sends the key as a header only, never in the URL or body", async () => {
    const fetch = mockFetch(201, { id: "x" });
    await api.createQuiz("abc", { provider: "openai", model: "gpt-5-mini", apiKey: KEY });
    const [url, init] = fetch.mock.calls[0];
    expect(url).toBe("/api/analyses/abc/quiz/");
    expect(init.headers["X-LLM-Key"]).toBe(KEY);
    expect(init.headers["X-Resume-Quest"]).toBe("1");
    expect(init.body).not.toContain(KEY);
    expect(url).not.toContain(KEY);
    expect(init.credentials).toBe("omit");
    expect(init.cache).toBe("no-store");
  });

  it("puts the file, provider and model in a multipart form", async () => {
    const fetch = mockFetch(201, { id: "x" });
    const file = new File(["%PDF-"], "cv.pdf");
    await api.analyse(file, { provider: "ollama", model: "", apiKey: "" });
    const [, init] = fetch.mock.calls[0];
    expect(init.body.get("file").name).toBe("cv.pdf");
    expect(init.body.get("provider")).toBe("ollama");
    expect(init.body.has("model")).toBe(false);
    expect(init.headers["X-LLM-Key"]).toBeUndefined();
  });

  it("turns error responses into ApiError with the server's message", async () => {
    mockFetch(401, { error: "invalid_key", detail: "The provider rejected the API key." });
    await expect(api.history()).rejects.toMatchObject({ status: 401, code: "invalid_key", message: "The provider rejected the API key." });
  });

  it("explains when the server can't be reached", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    const error = await api.history().catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.message).toMatch(/Can't reach the app server/);
  });

  it("handles 204 No Content", async () => {
    mockFetch(204);
    await expect(api.remove("abc")).resolves.toBeNull();
  });
});
