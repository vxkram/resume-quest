import { useState } from "react";
import { useParams } from "react-router";

import { api } from "../api";
import { ErrorNote } from "../components/ErrorNote";
import { Loading } from "../components/Loading";
import { Sprite } from "../components/Sprite";
import { Window } from "../components/Window";
import { useSession } from "../session";
import { NeedsModel } from "./NeedsModel";
import { CommandMenu } from "./Sheet";
import { useAnalysis } from "./useAnalysis";

const TIERS = [
  ["easy", "Warm-up"],
  ["medium", "Core"],
  ["hard", "Deep dive"],
];

export function Interview() {
  const { id } = useParams();
  const { analysis, setAnalysis, error: loadError } = useAnalysis(id);
  const session = useSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const generate = async () => {
    setBusy(true);
    setError(null);
    try {
      const { questions } = await api.interview(id, session.llm());
      setAnalysis({ ...analysis, interview: questions });
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  if (loadError) return <ErrorNote error={loadError} />;
  if (!analysis) return <p className="muted">Loading…</p>;
  const questions = analysis.interview;
  return (
    <>
      <CommandMenu id={id} current="interview" />
      {busy ? (
        <Loading title="Writing interview questions" steps={["Reading the résumé…", "Writing questions…", "Noting what good answers cover…"]} />
      ) : questions ? (
        <>
          {TIERS.map(([tier, label]) => {
            const list = questions.filter((q) => q.difficulty === tier);
            if (!list.length) return null;
            return (
              <Window key={tier} title={label} className="scrolls">
                {list.map((q, i) => (
                  <details key={i} className="scroll">
                    <summary>
                      <Sprite name="scroll" scale={2} />
                      <span>
                        <span className="tag">{q.skill}</span> {q.question}
                      </span>
                    </summary>
                    <p className="muted">A strong answer covers:</p>
                    <ul>{q.good_answer_covers.map((c) => <li key={c}>{c}</li>)}</ul>
                  </details>
                ))}
              </Window>
            );
          })}
          <Window title="Different questions">
            <ErrorNote error={error} />
            <NeedsModel action="Write new questions" onGo={generate} busy={busy} />
          </Window>
        </>
      ) : (
        <Window title="Interview questions">
          <p>
            Questions an interviewer could ask to check the skills on this résumé, from warm-up to deep dive, each with
            what a strong answer covers.
          </p>
          <ErrorNote error={error} />
          <NeedsModel action="Write questions" onGo={generate} busy={busy} />
        </Window>
      )}
    </>
  );
}
