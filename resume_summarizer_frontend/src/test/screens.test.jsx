import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "../api";
import { Quiz } from "../screens/Quiz";
import { Sheet } from "../screens/Sheet";
import { SessionProvider } from "../session";
import { ANALYSIS, PROVIDERS } from "./fixtures";

afterEach(() => vi.restoreAllMocks());

function renderAt(path, element, routePath) {
  return render(
    <SessionProvider initialProviders={PROVIDERS}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path={routePath} element={element} />
        </Routes>
      </MemoryRouter>
    </SessionProvider>,
  );
}

describe("status screen", () => {
  it("shows the class, skills, rank and evidence", async () => {
    vi.spyOn(api, "analysis").mockResolvedValue(ANALYSIS);
    const user = userEvent.setup();
    renderAt(`/sheet/${ANALYSIS.id}`, <Sheet />, "/sheet/:id");

    expect(await screen.findByRole("heading", { name: "Machine Learning Engineer" })).toBeInTheDocument();
    expect(screen.getByText("Level 3 (Mid) in retail")).toBeInTheDocument();
    expect(screen.getByLabelText("Rank A")).toBeInTheDocument();
    expect(screen.getByRole("meter", { name: "PyTorch: 70 of 100, Adept" })).toHaveAttribute("aria-valuenow", "70");
    expect(screen.getByText("Gap: Aug 2021 to Mar 2022 (7 months)")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /PyTorch/ }));
    expect(screen.getByText("Found: Used at work")).toBeInTheDocument();
    expect(screen.getByText("Not in résumé: Certification")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Databases 1/ }));
    expect(screen.queryByRole("button", { name: /PyTorch/ })).toBeNull();
    expect(screen.getByRole("button", { name: /Redis/ })).toBeInTheDocument();
  });
});

describe("quiz", () => {
  const QUIZ = {
    id: "q1",
    analysis_id: ANALYSIS.id,
    result: null,
    questions: [0, 1].map((i) => ({
      index: i, skill: "PyTorch", difficulty: "medium", question: `Question ${i + 1}?`, options: ["a", "b", "c", "d"],
    })),
  };

  it("plays through and shows claimed versus demonstrated", async () => {
    vi.spyOn(api, "analysis").mockResolvedValue(ANALYSIS);
    vi.spyOn(api, "createQuiz").mockResolvedValue(QUIZ);
    const submit = vi.spyOn(api, "submitQuiz").mockResolvedValue({
      ...QUIZ,
      result: {
        score: 50, correct: 1, total: 2, level: "Apprentice",
        questions: [
          { correct: true, chosen: 2, answer_index: 2, explanation: "c is right." },
          { correct: false, chosen: null, answer_index: 0, explanation: "a is right." },
        ],
        skills: [{ skill: "PyTorch", correct: 1, total: 2, demonstrated: 50, claimed: 70, verdict: "matches_claim" }],
      },
    });
    const user = userEvent.setup();
    renderAt(`/sheet/${ANALYSIS.id}/quiz`, <Quiz />, "/sheet/:id/quiz");

    await user.click(await screen.findByRole("button", { name: "Start quiz" }));
    expect(await screen.findByText("Question 1?")).toBeInTheDocument();
    await user.click(screen.getByRole("radio", { name: /C c/ }));
    expect(screen.getByRole("radio", { name: /C c/ })).toHaveAttribute("aria-checked", "true");
    await user.click(screen.getByRole("button", { name: "Next" }));
    await user.click(screen.getByRole("button", { name: "Submit answers" }));

    expect(submit).toHaveBeenCalledWith("q1", [2, null]);
    const row = (await screen.findByRole("row", { name: /PyTorch/ }));
    expect(within(row).getByText("Matches the résumé")).toBeInTheDocument();
    expect(screen.getByText(/Skipped/)).toBeInTheDocument();
  });
});
