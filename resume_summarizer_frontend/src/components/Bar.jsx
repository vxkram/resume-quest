// A segmented pixel gauge, like an RPG health bar. The level text says the same
// thing as the colour, so the colour is never the only signal.
export const LEVEL_CLASS = {
  Expert: "lv-expert", Adept: "lv-adept", Apprentice: "lv-apprentice", Novice: "lv-novice", Unproven: "lv-unproven",
};

export function Bar({ value, label, level, small = false }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div
      className={`bar ${small ? "bar-small" : ""} ${LEVEL_CLASS[level] ?? ""}`}
      role="meter"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      aria-label={label}
    >
      <div className="bar-fill" style={{ width: `${pct}%` }} />
    </div>
  );
}
