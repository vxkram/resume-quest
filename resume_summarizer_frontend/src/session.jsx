// Which provider and model to use, and the API keys, held in React state only.
//
// Keys are deliberately never written to localStorage, sessionStorage, IndexedDB,
// cookies or the URL. They vanish when the tab is closed or reloaded, and are
// forgotten automatically after a stretch of inactivity.
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { api } from "./api";

export const IDLE_FORGET_MS = 30 * 60 * 1000;
const PREFS = "resume-quest:llm"; // provider + model name only, never a key

const SessionContext = createContext(null);

function loadPrefs() {
  try {
    return JSON.parse(localStorage.getItem(PREFS)) ?? {};
  } catch {
    return {};
  }
}

export function maskKey(key) {
  if (!key) return "";
  return key.length > 12 ? `…${key.slice(-4)}` : "…";
}

// What the server says about where it runs; local defaults until it answers.
export const LOCAL_CONFIG = { hosted: false, save_hours: null, max_upload_mb: 5 };

export function SessionProvider({ children, initialProviders = null, initialConfig = LOCAL_CONFIG }) {
  const [config, setConfig] = useState(initialConfig);
  const [providers, setProviders] = useState(initialProviders);
  const [providersError, setProvidersError] = useState(null);
  const [provider, setProviderState] = useState(() => loadPrefs().provider ?? "ollama");
  const [models, setModels] = useState(() => loadPrefs().models ?? {});
  const [keys, setKeys] = useState({});
  const idleTimer = useRef(null);

  useEffect(() => {
    if (initialProviders) return;
    api.providers().then(setProviders, (error) => setProvidersError(error.message));
    api.config().then(setConfig, () => {});
  }, [initialProviders]);

  // A remembered provider may not be offered here (Ollama on the hosted site):
  // fall back to the first free one.
  useEffect(() => {
    if (providers?.length && !providers.some((p) => p.id === provider)) {
      setProviderState((providers.find((p) => p.free_tier) ?? providers[0]).id);
    }
  }, [providers, provider]);

  useEffect(() => {
    try {
      localStorage.setItem(PREFS, JSON.stringify({ provider, models }));
    } catch {
      // Storage blocked: preferences just won't be remembered.
    }
  }, [provider, models]);

  const forgetAllKeys = useCallback(() => setKeys({}), []);

  // Any key activity restarts the idle countdown.
  const touch = useCallback(() => {
    clearTimeout(idleTimer.current);
    idleTimer.current = setTimeout(forgetAllKeys, IDLE_FORGET_MS);
  }, [forgetAllKeys]);

  useEffect(() => () => clearTimeout(idleTimer.current), []);

  const value = useMemo(() => {
    const info = providers?.find((p) => p.id === provider) ?? null;
    return {
      config,
      providers,
      providersError,
      provider,
      info,
      setProvider: setProviderState,
      model: models[provider] ?? "",
      setModel: (model) => setModels((m) => ({ ...m, [provider]: model })),
      apiKey: keys[provider] ?? "",
      setApiKey: (key) => {
        setKeys((k) => ({ ...k, [provider]: key }));
        touch();
      },
      forgetKey: () => setKeys(({ [provider]: _, ...rest }) => rest),
      forgetAllKeys,
      ready: Boolean(info) && (!info.needs_key || Boolean(keys[provider])),
      // What an API call needs. Calling this counts as activity.
      llm: () => {
        touch();
        return { provider, model: models[provider] || info?.default_model || "", apiKey: info?.needs_key ? keys[provider] : "" };
      },
    };
  }, [config, providers, providersError, provider, models, keys, touch, forgetAllKeys]);

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const session = useContext(SessionContext);
  if (!session) throw new Error("useSession outside SessionProvider");
  return session;
}
