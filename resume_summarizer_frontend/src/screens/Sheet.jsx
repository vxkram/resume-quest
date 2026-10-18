import { useState } from "react";
import { Link, useParams } from "react-router";

import { Bar } from "../components/Bar";
import { ErrorNote } from "../components/ErrorNote";
import { Sprite } from "../components/Sprite";
import { Window } from "../components/Window";
import { CATEGORY_LABELS, EVIDENCE_LABELS, SENIORITY, SENIORITY_LEVEL } from "./labels";
import { useAnalysis } from "./useAnalysis";

export function CommandMenu({ id, current }) {
  const items = [
    ["sheet", `/sheet/${id}`, "Status"],
    ["quiz", `/sheet/${id}/quiz`, "Quiz"],
    ["interview", `/sheet/${id}/interview`, "Interview"],
    ["training", `/sheet/${id}/training`, "Prove it"],
  ];
  return (
    <nav className="command-menu window" aria-label="Analysis sections">
      {items.map(([key, to, label]) => (
        <Link key={key} to={to} className="command" aria-current={current === key ? "page" : undefined}>
          {label}
        </Link>
      ))}
    </nav>
  );
}

function SkillRow({ skill }) {
  const [open, setOpen] = useState(false);
  const panel = `evidence-${skill.name.replace(/\W+/g, "-")}`;
  return (
    <li className="skill">
      <button type="button" className="skill-head" aria-expanded={open} aria-controls={panel} onClick={() => setOpen(!open)}>
        <span className="skill-name">{skill.name}</span>
        <span className="skill-level">
          {skill.level} <span className="muted">{skill.score}</span>
        </span>
        <Bar value={skill.score} level={skill.level} label={`${skill.name}: ${skill.score} of 100, ${skill.level}`} />
      </button>
      {open && (
        <ul className="evidence" id={panel}>
          {skill.evidence.map((e, i) => (
            <li key={i} className={e.verified ? "ok" : "bad"}>
              <span className="evidence-kind">
                {e.verified ? "Found" : e.problem === "off_topic" ? `Doesn't mention ${skill.name}` : "Not in résumé"}:{" "}
                {EVIDENCE_LABELS[e.type]}
              </span>
              <q>{e.quote}</q>
            </li>
          ))}
          {skill.rejected_count > 0 && (
            <li className="muted">Crossed-out quotes came from the model but aren't in the résumé or aren't about this skill, so they don't count.</li>
          )}
        </ul>
      )}
    </li>
  );
}

function Skills({ skills, categories }) {
  const [filter, setFilter] = useState("all");
  const shown = filter === "all" ? skills : skills.filter((s) => s.category === filter);
  return (
    <Window title="Skills" className="skills">
      <div className="tabs" role="group" aria-label="Filter by category">
        <button type="button" className="tab" aria-pressed={filter === "all"} onClick={() => setFilter("all")}>
          All {skills.length}
        </button>
        {categories.map((c) => (
          <button key={c.category} type="button" className="tab" aria-pressed={filter === c.category} onClick={() => setFilter(c.category)}>
            {CATEGORY_LABELS[c.category]} {c.count}
          </button>
        ))}
      </div>
      <ul className="skill-list">
        {shown.map((s) => (
          <SkillRow key={s.name} skill={s} />
        ))}
      </ul>
      <p className="hint">
        Scores come from evidence in the résumé: paid work 35, a measured result 25, a project 25, a certification 20,
        a skills-list entry 10, plus up to 10 for repeat evidence. A skill that's only listed tops out at 30.
      </p>
    </Window>
  );
}

function Quality({ quality }) {
  return (
    <Window title="Résumé rank" className="quality">
      <div className="rank-row">
        <span className={`rank rank-${quality.rank}`} aria-label={`Rank ${quality.rank}`}>
          {quality.rank}
        </span>
        <div>
          <p className="big-number">{quality.score}<small>/100</small></p>
          <p className="muted">
            {quality.word_count} words, {quality.bullet_count} bullets
          </p>
        </div>
      </div>
      <ul className="checks">
        {quality.checks.map((c) => (
          <li key={c.id} className={c.passed ? "ok" : "bad"}>
            <span className="check-box" aria-hidden="true" />
            <span>
              <span className="visually-hidden">{c.passed ? "Passed: " : "Failed: "}</span>
              {c.label}
              {!c.passed && <small>{c.tip}</small>}
            </span>
          </li>
        ))}
      </ul>
      <p className="muted">
        {quality.quantified_pct}% of bullets have numbers. {quality.action_verb_pct}% start with an action verb.
      </p>
      {quality.gaps.map((g) => (
        <p key={g.from} className="muted">
          Gap: {g.from} to {g.to} ({g.months} months)
        </p>
      ))}
    </Window>
  );
}

export function Sheet() {
  const { id } = useParams();
  const { analysis, error } = useAnalysis(id);
  if (error) return <Window title="Save file not found"><ErrorNote error={error} /><Link to="/">Start a new one</Link></Window>;
  if (!analysis) return <p className="muted">Loading…</p>;
  const { profile } = analysis;
  const [top, ...others] = profile.role_fits;

  return (
    <>
      <CommandMenu id={id} current="sheet" />
      <div className="sheet-grid">
        <Window className="status">
          <div className="status-head">
            <div className="portrait">
              <Sprite name="hero" scale={6} />
            </div>
            <div>
              <p className="muted">Class</p>
              <h1 className="class-name">{top.title}</h1>
              <p>
                Level {SENIORITY_LEVEL[profile.seniority]} ({SENIORITY[profile.seniority]}) in {profile.domain}
              </p>
            </div>
            <div className="power">
              <p className="big-number">{analysis.power_level}</p>
              <p className="muted">Power</p>
            </div>
          </div>
          <p className="headline">{profile.headline}</p>
          <p>{profile.summary}</p>
          <p className="muted">
            Read by {analysis.model} from {analysis.file_name}
          </p>
        </Window>

        <Quality quality={analysis.quality} />

        <Skills skills={analysis.skills} categories={analysis.categories} />

        <Window title="Class fit" className="roles">
          <ul className="role-list">
            {[top, ...others].map((r) => (
              <li key={r.title}>
                <div className="role-head">
                  <strong>{r.title}</strong>
                  <span>{r.confidence}%</span>
                </div>
                <Bar value={r.confidence} small level="Adept" label={`${r.title}: ${r.confidence}% fit`} />
                <p className="muted">{r.rationale}</p>
              </li>
            ))}
          </ul>
          <h3>Strengths</h3>
          <ul className="plain">{profile.strengths.map((s) => <li key={s}>{s}</li>)}</ul>
          <h3>Gaps</h3>
          <ul className="plain">{profile.gaps.map((g) => <li key={g}>{g}</li>)}</ul>
        </Window>
      </div>
    </>
  );
}
