import { useEffect, useState } from "react";
import { Link } from "react-router";

import { api } from "../api";
import { ErrorNote } from "../components/ErrorNote";
import { Window } from "../components/Window";
import { SENIORITY } from "./labels";

const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });

function Slot({ save, onDelete }) {
  const [confirming, setConfirming] = useState(false);
  return (
    <li className="slot">
      <Link to={`/sheet/${save.id}`} className="slot-main">
        <strong>{save.top_role}</strong>
        <span>
          {SENIORITY[save.seniority]}, power {save.power_level}, rank {save.quality_rank}
        </span>
        <small className="muted">
          {save.file_name}, {dateFormat.format(new Date(save.created_at))}
        </small>
      </Link>
      {confirming ? (
        <span className="row">
          <button type="button" className="btn btn-small btn-danger" onClick={() => onDelete(save.id)}>
            Delete for good
          </button>
          <button type="button" className="btn btn-small" onClick={() => setConfirming(false)}>
            Keep
          </button>
        </span>
      ) : (
        <button type="button" className="btn btn-small" onClick={() => setConfirming(true)} aria-label={`Delete ${save.file_name}`}>
          Delete
        </button>
      )}
    </li>
  );
}

export function Saves() {
  const [saves, setSaves] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    api.history().then(setSaves, setError);
  }, []);

  const remove = async (id) => {
    try {
      await api.remove(id);
      setSaves((s) => s.filter((x) => x.id !== id));
    } catch (e) {
      setError(e);
    }
  };

  return (
    <Window title="Save files">
      <p className="muted">
        Analyses are stored in a local database on this computer, along with the résumé's text. Deleting one removes
        both.
      </p>
      <ErrorNote error={error} />
      {saves && saves.length === 0 && (
        <p>
          No save files yet. <Link to="/">Analyse a résumé</Link> to start one.
        </p>
      )}
      {saves && saves.length > 0 && (
        <ul className="slots">
          {saves.map((s) => <Slot key={s.id} save={s} onDelete={remove} />)}
        </ul>
      )}
    </Window>
  );
}
