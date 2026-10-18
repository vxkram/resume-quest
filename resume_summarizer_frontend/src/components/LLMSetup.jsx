import { useEffect, useId, useState } from "react";

import { api } from "../api";
import { maskKey, useSession } from "../session";
import { ErrorNote } from "./ErrorNote";
import { Sprite } from "./Sprite";

const GEM_COLORS = {
  openai: "#00e436", anthropic: "#ffa300", gemini: "#29adff", groq: "#ff004d",
  openrouter: "#83769c", ollama: "#ff77a8", fake: "#c2c3c7",
};

function costNote(p) {
  if (!p.needs_key) return "Free, runs on this computer";
  return p.free_tier ? "Free API key" : "Paid API key";
}

export function ProviderPicker() {
  const { providers, providersError, provider, setProvider } = useSession();
  if (providersError) return <p className="error">{providersError}</p>;
  if (!providers) return <p className="muted">Loading models…</p>;
  return (
    <fieldset className="providers">
      <legend>Model provider</legend>
      {providers.map((p) => (
        <label key={p.id} className={`provider ${provider === p.id ? "is-on" : ""}`}>
          <input type="radio" name="provider" value={p.id} checked={provider === p.id} onChange={() => setProvider(p.id)} />
          <Sprite name="gem" scale={3} color={GEM_COLORS[p.id]} />
          <span>{p.label}</span>
          <small>{costNote(p)}</small>
        </label>
      ))}
    </fieldset>
  );
}

export function ModelField() {
  const { info, model, setModel, apiKey, provider } = useSession();
  const [options, setOptions] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const id = useId();

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setOptions((await api.models(provider, info.needs_key ? apiKey : "")).models);
    } catch (e) {
      setError(e);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  // Local models can be listed straight away; cloud ones need the key first.
  useEffect(() => {
    setOptions([]);
    setError(null);
    if (info && !info.needs_key) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [provider, info?.needs_key]);

  if (!info) return null;
  return (
    <div className="field">
      <label htmlFor={id}>Model</label>
      <div className="row">
        <input
          id={id}
          list={`${id}-list`}
          value={model}
          placeholder={info.default_model}
          onChange={(e) => setModel(e.target.value.trim())}
          autoComplete="off"
          spellCheck={false}
        />
        {info.needs_key && (
          <button type="button" className="btn btn-small" onClick={load} disabled={!apiKey || loading}>
            {loading ? "Loading…" : "List models"}
          </button>
        )}
      </div>
      <datalist id={`${id}-list`}>
        {options.map((m) => (
          <option key={m} value={m} />
        ))}
      </datalist>
      <p className="hint">Leave empty to use {info.default_model}.</p>
      <ErrorNote error={error} />
    </div>
  );
}

export function KeyField() {
  const { info, apiKey, setApiKey, forgetKey } = useSession();
  const [draft, setDraft] = useState("");
  const [show, setShow] = useState(false);
  const id = useId();
  if (!info?.needs_key) return null;

  const save = () => {
    const key = draft.trim();
    if (key) setApiKey(key);
    setDraft("");
    setShow(false);
  };

  return (
    <div className="field key-field">
      <label htmlFor={id}>{info.label} API key</label>
      {apiKey ? (
        <div className="row key-set">
          <Sprite name="lock" scale={3} />
          <span>
            Key in memory <code>{maskKey(apiKey)}</code>
          </span>
          <button type="button" className="btn btn-small" onClick={forgetKey}>
            Forget key
          </button>
        </div>
      ) : (
        <div className="row">
          <Sprite name="lock" scale={3} />
          {/* Not inside a <form>, so password managers don't offer to save it. */}
          <input
            id={id}
            type={show ? "text" : "password"}
            value={draft}
            placeholder={info.key_hint}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), save())}
            autoComplete="off"
            autoCapitalize="off"
            autoCorrect="off"
            spellCheck={false}
            data-1p-ignore="true"
            data-lpignore="true"
            data-bwignore="true"
            data-form-type="other"
          />
          <button type="button" className="btn btn-small" onClick={() => setShow((s) => !s)} aria-pressed={show}>
            {show ? "Hide" : "Show"}
          </button>
          <button type="button" className="btn btn-small btn-go" onClick={save} disabled={!draft.trim()}>
            Use key
          </button>
        </div>
      )}
      {info.key_url && (
        <p className="hint">
          <a href={info.key_url} target="_blank" rel="noopener noreferrer">
            {info.free_tier ? "Get a free key" : "Get a key"}
          </a>{" "}
          from {info.label}.
        </p>
      )}
      <p className="hint">
        Held in this tab's memory only: never saved to disk or browser storage. It goes to this app's local server,
        which hands it to {info.label} for each request and keeps no copy. Reloading the page, or 30 idle minutes,
        forgets it.
      </p>
    </div>
  );
}

// Everything needed before an AI call, in one block.
export function LLMSetup() {
  return (
    <div className="llm-setup">
      <ProviderPicker />
      <KeyField />
      <ModelField />
    </div>
  );
}
