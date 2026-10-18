import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../api";
import { KeyField, ModelField, ProviderPicker } from "../components/LLMSetup";
import { IDLE_FORGET_MS, maskKey, SessionProvider, useSession } from "../session";
import { KEY, PROVIDERS } from "./fixtures";

function storageText() {
  const dump = (s) => Object.keys(s).map((k) => `${k}=${s.getItem(k)}`).join(";");
  return dump(localStorage) + dump(sessionStorage) + document.cookie;
}

function Probe() {
  const { llm } = useSession();
  return <button onClick={() => (window.__llm = llm())}>probe</button>;
}

function setup() {
  return render(
    <SessionProvider initialProviders={PROVIDERS}>
      <ProviderPicker />
      <KeyField />
      <ModelField />
      <Probe />
    </SessionProvider>,
  );
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  vi.spyOn(api, "models").mockResolvedValue({ models: ["qwen3.5:4b"] });
});
afterEach(() => vi.restoreAllMocks());

describe("API key handling in the browser", () => {
  it("keeps the key in memory only and shows just its last four characters", async () => {
    const user = userEvent.setup();
    setup();
    await user.click(screen.getByLabelText(/OpenAI/));
    const input = screen.getByLabelText("OpenAI API key");
    expect(input).toHaveAttribute("type", "password");
    expect(input).toHaveAttribute("autocomplete", "off");
    expect(input).toHaveAttribute("spellcheck", "false");
    expect(input.closest("form")).toBeNull(); // no form, so no "save password?" prompt

    await user.type(input, KEY);
    await user.click(screen.getByRole("button", { name: "Use key" }));

    expect(screen.getByText(/Key in memory/)).toHaveTextContent("…WXYZ");
    expect(document.body.innerHTML).not.toContain(KEY);
    expect(storageText()).not.toContain(KEY);
    expect(storageText()).toContain("openai"); // the provider choice is remembered, the key is not

    await user.click(screen.getByText("probe"));
    expect(window.__llm.apiKey).toBe(KEY);
  });

  it("forgets the key on request", async () => {
    const user = userEvent.setup();
    setup();
    await user.click(screen.getByLabelText(/OpenAI/));
    await user.type(screen.getByLabelText("OpenAI API key"), KEY);
    await user.click(screen.getByRole("button", { name: "Use key" }));
    await user.click(screen.getByRole("button", { name: "Forget key" }));
    await user.click(screen.getByText("probe"));
    expect(window.__llm.apiKey).toBeFalsy();
    expect(screen.getByLabelText("OpenAI API key")).toHaveValue("");
  });

  it("forgets the key after 30 idle minutes", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    setup();
    await user.click(screen.getByLabelText(/OpenAI/));
    await user.type(screen.getByLabelText("OpenAI API key"), KEY);
    await user.click(screen.getByRole("button", { name: "Use key" }));
    expect(screen.getByText(/Key in memory/)).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(IDLE_FORGET_MS + 1000));
    expect(screen.queryByText(/Key in memory/)).toBeNull();
    vi.useRealTimers();
  });

  it("never sends a key for a local provider", async () => {
    const user = userEvent.setup();
    setup();
    await user.click(screen.getByLabelText(/Ollama/));
    expect(screen.queryByLabelText(/^OpenAI API key$/)).toBeNull();
    expect(document.querySelector("input[type=password]")).toBeNull();
    await user.click(screen.getByText("probe"));
    expect(window.__llm).toEqual({ provider: "ollama", model: "qwen3.5:4b", apiKey: "" });
  });

  it("labels free and paid providers and links to where keys come from", async () => {
    const user = userEvent.setup();
    setup();
    expect(screen.getByText("Free API key")).toBeInTheDocument();
    expect(screen.getByText("Paid API key")).toBeInTheDocument();
    await user.click(screen.getByLabelText(/Groq/));
    const link = screen.getByRole("link", { name: "Get a free key" });
    expect(link).toHaveAttribute("href", "https://console.groq.com/keys");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("masks keys", () => {
    expect(maskKey(KEY)).toBe("…WXYZ");
    expect(maskKey("short")).toBe("…");
    expect(maskKey("")).toBe("");
  });
});
