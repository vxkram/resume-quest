import { LLMSetup } from "../components/LLMSetup";
import { useSession } from "../session";

// Shown before an AI call when there's no usable provider set up in this tab yet
// (for example after a reload, which forgets the key).
export function NeedsModel({ action, onGo, busy }) {
  const session = useSession();
  return (
    <div className="needs-model">
      <LLMSetup />
      <button type="button" className="btn btn-go btn-big" onClick={onGo} disabled={!session.ready || busy}>
        {action}
      </button>
    </div>
  );
}
