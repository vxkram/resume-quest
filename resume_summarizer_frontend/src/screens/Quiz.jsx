import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { api } from "../api";
import { Bar } from "../components/Bar";
import { ErrorNote } from "../components/ErrorNote";
import { Loading } from "../components/Loading";
import { Sprite } from "../components/Sprite";
import { Window } from "../components/Window";
import { useSession } from "../session";
import { VERDICTS } from "./labels";
import { NeedsModel } from "./NeedsModel";
import { CommandMenu } from "./Sheet";
import { useAnalysis } from "./useAnalysis";

const STEPS = ["Picking the skills to test…", "Writing questions…", "Shuffling the answers…", "Almost there…"];
const LETTERS = ["A", "B", "C", "D"];

function Battle({ quiz, onDone }) {
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState(() => quiz.questions.map(() => null));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const q = quiz.questions[index];
  const last = index === quiz.questions.length - 1;

  const choose = (option) => setAnswers((a) => a.map((v, i) => (i === index ? option : v)));
  const submit = async () => {
    setBusy(true);
    try {
      onDone(await api.submitQuiz(quiz.id, answers));
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  return (
    <div className="battle">
      <div className="arena" aria-hidden="true">
        <Sprite name="slime" scale={8} className="enemy" />
        <Sprite name="hero" scale={6} className="player" />
      </div>
      <Window className="dialog">
        <p className="muted">
          Question {index + 1} of {quiz.questions.length}: a {q.difficulty} {q.skill} question
        </p>
        <h2 className="question">{q.question}</h2>
        <div className="options" role="radiogroup" aria-label="Answers">
          {q.options.map((option, i) => (
            <button
              key={i}
              type="button"
              role="radio"
              aria-checked={answers[index] === i}
              className="option"
              onClick={() => choose(i)}
            >
              <span className="option-letter">{LETTERS[i]}</span> {option}
            </button>
          ))}
        </div>
        <ErrorNote error={error} />
        <div className="actions">
          <button type="button" className="btn" disabled={index === 0} onClick={() => setIndex(index - 1)}>
            Back
          </button>
          {last ? (
            <button type="button" className="btn btn-go" onClick={submit} disabled={busy}>
              Submit answers
            </button>
          ) : (
            <button type="button" className="btn btn-go" onClick={() => setIndex(index + 1)}>
              {answers[index] === null ? "Skip" : "Next"}
            </button>
          )}
        </div>
      </Window>
    </div>
  );
}

function Results({ quiz, onRetry }) {
  const { result } = quiz;
  return (
    <>
      <Window title="Results" className="results">
        <div className="rank-row">
          <p className="big-number">
            {result.correct}<small>/{result.total}</small>
          </p>
          <p>
            {result.score}% correct: {result.level}
          </p>
        </div>
        <table className="claims">
          <caption className="visually-hidden">Claimed versus demonstrated skill</caption>
          <thead>
            <tr>
              <th scope="col">Skill</th>
              <th scope="col">Résumé says</th>
              <th scope="col">Quiz shows</th>
              <th scope="col">Verdict</th>
            </tr>
          </thead>
          <tbody>
            {result.skills.map((s) => (
              <tr key={s.skill}>
                <th scope="row">{s.skill}</th>
                <td>
                  {s.claimed ?? "?"}
                  {s.claimed != null && <Bar small value={s.claimed} level="Adept" label={`Résumé: ${s.claimed}`} />}
                </td>
                <td>
                  {s.demonstrated} ({s.correct}/{s.total})
                  <Bar small value={s.demonstrated} level="Expert" label={`Quiz: ${s.demonstrated}`} />
                </td>
                <td>{VERDICTS[s.verdict] ?? "Not on the résumé"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="hint">One to three questions per skill is a small sample: treat verdicts as a prompt to dig in, not a judgement.</p>
        <button type="button" className="btn btn-go" onClick={onRetry}>
          New quiz
        </button>
      </Window>
      <Window title="Answers" className="review">
        <ol>
          {quiz.questions.map((q, i) => {
            const r = result.questions[i];
            return (
              <li key={i} className={r.correct ? "ok" : "bad"}>
                <p className="question-small">{q.question}</p>
                <p>
                  {r.correct ? "Correct" : r.chosen === null ? "Skipped" : `You chose ${LETTERS[r.chosen]}`}. Answer:{" "}
                  {LETTERS[r.answer_index]}, {q.options[r.answer_index]}
                </p>
                <p className="muted">{r.explanation}</p>
              </li>
            );
          })}
        </ol>
      </Window>
    </>
  );
}

export function Quiz() {
  const { id } = useParams();
  const { analysis, error: loadError } = useAnalysis(id);
  const session = useSession();
  const [quiz, setQuiz] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  // Resume the latest quiz if there is one.
  useEffect(() => {
    const latest = analysis?.latest_quiz;
    if (latest && !quiz) api.quiz(latest.id).then(setQuiz, setError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analysis]);

  const create = async () => {
    setBusy(true);
    setError(null);
    try {
      setQuiz(await api.createQuiz(id, session.llm()));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  if (loadError) return <ErrorNote error={loadError} />;
  if (!analysis) return <p className="muted">Loading…</p>;
  return (
    <>
      <CommandMenu id={id} current="quiz" />
      {busy ? (
        <Loading title="Summoning questions" steps={STEPS} />
      ) : quiz?.result ? (
        <Results quiz={quiz} onRetry={() => setQuiz({})} />
      ) : quiz?.questions ? (
        <Battle quiz={quiz} onDone={setQuiz} />
      ) : (
        <Window title="Quiz">
          <p>
            Eight multiple-choice questions on the strongest skills this résumé claims, harder where it claims more. The
            answers stay on the server until you submit.
          </p>
          <ErrorNote error={error} />
          <NeedsModel action="Start quiz" onGo={create} busy={busy} />
          <p className="hint">
            <Link to={`/sheet/${id}`}>Back to the status screen</Link>
          </p>
        </Window>
      )}
    </>
  );
}
