import { useRef, useState } from "react";
import { useNavigate } from "react-router";

import { api } from "../api";
import { ErrorNote } from "../components/ErrorNote";
import { LLMSetup } from "../components/LLMSetup";
import { Loading } from "../components/Loading";
import { Window } from "../components/Window";
import { useSession } from "../session";

const MAX_BYTES = 5 * 1024 * 1024;
const STEPS = [
  "Reading the résumé…",
  "Working out which roles it's aimed at…",
  "Collecting evidence for each skill…",
  "Checking every quote against the résumé…",
  "Scoring skills and the résumé itself…",
  "Still going. Local models can take a minute.",
];

export function Title() {
  const session = useSession();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const input = useRef(null);

  const pick = (chosen) => {
    setError(null);
    if (!chosen) return;
    if (!/\.(pdf|docx)$/i.test(chosen.name)) return setError(new Error("Choose a PDF or DOCX file."));
    if (chosen.size > MAX_BYTES) return setError(new Error("That file is over the 5 MB limit."));
    setFile(chosen);
  };

  const start = async () => {
    setBusy(true);
    setError(null);
    try {
      const analysis = await api.analyse(file, session.llm());
      navigate(`/sheet/${analysis.id}`, { state: { analysis } });
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  if (busy) return <Loading title="Analysing" steps={STEPS} />;

  return (
    <>
      <header className="hero">
        <h1 className="logo">Résumé Quest</h1>
        <p className="lede">
          Drop in a résumé. Find out which roles it's aimed at, how strong each skill really is, and where to prove it.
        </p>
      </header>

      <Window className="setup" title="New game">
        <ol className="steps">
          <li>
            <h3>Choose who reads it</h3>
            <LLMSetup />
          </li>
          <li>
            <h3>Insert résumé</h3>
            <label
              className={`cartridge ${dragging ? "is-dragging" : ""} ${file ? "has-file" : ""}`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                pick(e.dataTransfer.files[0]);
              }}
            >
              <input
                ref={input}
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(e) => pick(e.target.files[0])}
              />
              <span className="cartridge-slot" aria-hidden="true" />
              {file ? (
                <span className="cartridge-label">
                  <strong>{file.name}</strong>
                  <small>{Math.ceil(file.size / 1024)} KB. Click to change.</small>
                </span>
              ) : (
                <span className="cartridge-label">
                  <strong>Drop a PDF or DOCX here</strong>
                  <small>or click to choose (5 MB max)</small>
                </span>
              )}
            </label>
          </li>
        </ol>
        <ErrorNote error={error} />
        <div className="actions">
          <button type="button" className="btn btn-go btn-big" onClick={start} disabled={!file || !session.ready}>
            Analyse résumé
          </button>
          {!session.ready && session.info?.needs_key && <p className="hint">Add your {session.info.label} key first.</p>}
        </div>
      </Window>
    </>
  );
}
