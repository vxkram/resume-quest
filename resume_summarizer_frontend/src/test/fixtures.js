export const PROVIDERS = [
  { id: "openai", label: "OpenAI", needs_key: true, default_model: "gpt-5-mini", key_hint: "sk-…", free_tier: false, key_url: "https://platform.openai.com/api-keys" },
  { id: "groq", label: "Groq", needs_key: true, default_model: "openai/gpt-oss-120b", key_hint: "gsk_…", free_tier: true, key_url: "https://console.groq.com/keys" },
  { id: "ollama", label: "Ollama (local)", needs_key: false, default_model: "qwen3.5:4b", key_hint: "" },
];

export const KEY = "sk-proj-TESTKEY0123456789abcdefghijWXYZ";

export const ANALYSIS = {
  id: "11111111-1111-1111-1111-111111111111",
  created_at: "2026-10-18T10:00:00Z",
  file_name: "sample_resume.pdf",
  provider: "ollama",
  model: "qwen3.5:4b",
  headline: "ML engineer",
  top_role: "Machine Learning Engineer",
  seniority: "mid",
  power_level: 76,
  quality_rank: "A",
  profile: {
    headline: "ML engineer who ships recommendation models.",
    summary: "Four years of production ML.",
    seniority: "mid",
    domain: "retail",
    role_fits: [
      { title: "Machine Learning Engineer", confidence: 95, rationale: "Ships models." },
      { title: "Data Scientist", confidence: 70, rationale: "Forecasting work." },
    ],
    strengths: ["Measured impact"],
    gaps: ["No leadership title"],
  },
  skills: [
    {
      name: "PyTorch", category: "data_ml", score: 70, level: "Adept", verified_count: 2, rejected_count: 1,
      evidence: [
        { type: "job", quote: "Built a PyTorch recommendation model", verified: true, problem: null, source: "model" },
        { type: "cert", quote: "PyTorch certified wizard", verified: false, problem: "not_found", source: "model" },
      ],
    },
    { name: "Redis", category: "database", score: 10, level: "Novice", verified_count: 1, rejected_count: 0,
      evidence: [{ type: "listed", quote: "Redis", verified: true, problem: null, source: "scan" }] },
  ],
  categories: [
    { category: "data_ml", average: 70, count: 1 },
    { category: "database", average: 10, count: 1 },
  ],
  quality: {
    score: 85, rank: "A", word_count: 300, bullet_count: 10, quantified_pct: 60, action_verb_pct: 80,
    sections: {}, contact: {}, gaps: [{ from: "Aug 2021", to: "Mar 2022", months: 7 }],
    checks: [
      { id: "email", label: "Email address", passed: true, tip: "" },
      { id: "length", label: "Length 350-1100 words", passed: false, tip: "Aim for 350-1100 words." },
    ],
  },
  training: { by_skill: [], general: [{ platform: "Exercism", title: "Tracks", url: "https://exercism.org/tracks" }] },
  interview: null,
  latest_quiz: null,
};
