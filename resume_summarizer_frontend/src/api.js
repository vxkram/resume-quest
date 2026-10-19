// The only place the app talks to the server. The API key, when there is one, is
// added as the X-LLM-Key header on the requests that need it and nowhere else:
// never in a URL, never in a body, never in storage.
//
// Every request also carries this browser's save token (X-Save-Token). On the
// hosted site the server uses it to show each browser only its own saves; run
// locally, the server ignores it. It is a random value, not a secret about you.

const SAVE_TOKEN = "resume-quest:save-token";
let memoryToken = null;

function newToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function saveToken() {
  try {
    let token = localStorage.getItem(SAVE_TOKEN);
    if (!token) {
      token = newToken();
      localStorage.setItem(SAVE_TOKEN, token);
    }
    return token;
  } catch {
    // Storage blocked: saves last as long as this tab.
    memoryToken ??= newToken();
    return memoryToken;
  }
}

export class ApiError extends Error {
  constructor(status, code, detail) {
    super(detail);
    this.status = status;
    this.code = code;
  }
}

async function request(path, { method = "GET", json, form, apiKey } = {}) {
  const headers = { "X-Resume-Quest": "1", "X-Save-Token": saveToken() };
  if (apiKey) headers["X-LLM-Key"] = apiKey;
  let body;
  if (form) {
    body = form;
  } else if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  }
  let response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      body,
      credentials: "omit",
      cache: "no-store",
      referrerPolicy: "no-referrer",
    });
  } catch {
    throw new ApiError(0, "offline", "Can't reach the app server. Is it running?");
  }
  if (response.status === 204) return null;
  let data = null;
  try {
    data = await response.json();
  } catch {
    // Non-JSON error page; fall through to the generic message.
  }
  if (!response.ok) {
    throw new ApiError(response.status, data?.error ?? "error", data?.detail ?? `Request failed (${response.status}).`);
  }
  return data;
}

// `llm` is { provider, model, apiKey } from the session.
const llmBody = ({ provider, model }) => ({ provider, model });

export const api = {
  config: () => request("/config/"),
  providers: () => request("/providers/"),
  models: (provider, apiKey) => request(`/providers/${provider}/models/`, { apiKey }),
  analyse(file, llm) {
    const form = new FormData();
    form.append("file", file);
    form.append("provider", llm.provider);
    if (llm.model) form.append("model", llm.model);
    return request("/analyses/", { method: "POST", form, apiKey: llm.apiKey });
  },
  history: () => request("/analyses/"),
  analysis: (id) => request(`/analyses/${id}/`),
  remove: (id) => request(`/analyses/${id}/`, { method: "DELETE" }),
  createQuiz: (id, llm) => request(`/analyses/${id}/quiz/`, { method: "POST", json: llmBody(llm), apiKey: llm.apiKey }),
  quiz: (quizId) => request(`/quizzes/${quizId}/`),
  submitQuiz: (quizId, answers) => request(`/quizzes/${quizId}/submit/`, { method: "POST", json: { answers } }),
  interview: (id, llm) => request(`/analyses/${id}/interview/`, { method: "POST", json: llmBody(llm), apiKey: llm.apiKey }),
};
