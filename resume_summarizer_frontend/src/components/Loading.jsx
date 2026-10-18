import { useEffect, useState } from "react";

import { Window } from "./Window";

// Local models can take a minute; say what is happening and how long it has been.
export function Loading({ title, steps }) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);
  const step = steps[Math.min(Math.floor(seconds / 6), steps.length - 1)];
  return (
    <Window title={title} className="loading" aria-live="polite">
      <div className="loading-bar" aria-hidden="true">
        <div className="loading-run" />
      </div>
      <p>{step}</p>
      <p className="muted">{seconds}s</p>
    </Window>
  );
}
