import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api, saveToken } from "../api";
import { Saves } from "../screens/Saves";
import { SessionProvider, useSession } from "../session";
import { PROVIDERS } from "./fixtures";

const HOSTED = { hosted: true, save_hours: 24, max_upload_mb: 4 };
const CLOUD_ONLY = PROVIDERS.filter((p) => p.id !== "ollama");

beforeEach(() => localStorage.clear());
afterEach(() => vi.restoreAllMocks());

describe("save token", () => {
  it("is random, URL-safe, kept for this browser and sent on every request", async () => {
    const token = saveToken();
    expect(token).toMatch(/^[A-Za-z0-9_-]{43}$/);
    expect(saveToken()).toBe(token);

    const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("[]", { status: 200 }));
    await api.history();
    expect(fetch.mock.calls[0][1].headers["X-Save-Token"]).toBe(token);

    localStorage.clear();
    expect(saveToken()).not.toBe(token);
  });
});

describe("hosted site", () => {
  function ShowProvider() {
    return <p>provider: {useSession().provider}</p>;
  }

  it("falls back to a free provider when the remembered one isn't offered", async () => {
    localStorage.setItem("resume-quest:llm", JSON.stringify({ provider: "ollama", models: {} }));
    render(
      <SessionProvider initialProviders={CLOUD_ONLY} initialConfig={HOSTED}>
        <ShowProvider />
      </SessionProvider>,
    );
    expect(await screen.findByText("provider: groq")).toBeInTheDocument();
  });

  it("explains that saves are private to this browser and expire", async () => {
    vi.spyOn(api, "history").mockResolvedValue([]);
    render(
      <SessionProvider initialProviders={CLOUD_ONLY} initialConfig={HOSTED}>
        <MemoryRouter>
          <Saves />
        </MemoryRouter>
      </SessionProvider>,
    );
    expect(screen.getByText(/kept on this site's server for 24 hours/)).toBeInTheDocument();
    expect(screen.getByText(/only this browser can see them/)).toBeInTheDocument();
    expect(await screen.findByText(/No save files yet/)).toBeInTheDocument();
  });
});
