import { useParams } from "react-router";

import { Bar } from "../components/Bar";
import { ErrorNote } from "../components/ErrorNote";
import { Window } from "../components/Window";
import { CommandMenu } from "./Sheet";
import { useAnalysis } from "./useAnalysis";

function TestLink({ test }) {
  return (
    <li>
      <a href={test.url} target="_blank" rel="noopener noreferrer">
        {test.title}
      </a>{" "}
      <span className="muted">on {test.platform}</span>
    </li>
  );
}

export function Training() {
  const { id } = useParams();
  const { analysis, error } = useAnalysis(id);
  if (error) return <ErrorNote error={error} />;
  if (!analysis) return <p className="muted">Loading…</p>;
  const { by_skill: bySkill, general } = analysis.training;
  return (
    <>
      <CommandMenu id={id} current="training" />
      <Window title="Where to prove it">
        <p>
          Real tests and certifications for the skills on this résumé, weakest evidence first. These links are picked by
          hand, not written by the AI.
        </p>
        {bySkill.length === 0 && <p className="muted">None of these skills have a matching test yet. Try the general ones below.</p>}
        <ul className="training">
          {bySkill.map((entry) => (
            <li key={entry.skill} className="training-skill">
              <div className="role-head">
                <strong>{entry.skill}</strong>
                <span>
                  {entry.level} {entry.score}
                </span>
              </div>
              <Bar small value={entry.score} level={entry.level} label={`${entry.skill}: ${entry.score}`} />
              <ul className="plain">{entry.tests.map((t) => <TestLink key={t.url} test={t} />)}</ul>
            </li>
          ))}
        </ul>
      </Window>
      <Window title="For any skill">
        <ul className="plain">{general.map((t) => <TestLink key={t.url} test={t} />)}</ul>
      </Window>
    </>
  );
}
