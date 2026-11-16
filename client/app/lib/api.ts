// Thin client for the FastAPI backend. All requests go to /api/* which
// Next.js proxies to the backend (see next.config.mjs), so there is no CORS
// and no hard-coded backend host in the browser bundle.

export interface Config {
  site_keys: { recaptcha: string; hcaptcha: string; turnstile: string };
  cost_model: { custom_solve_usd: number; thirdparty_solve_usd: number };
}

export interface SolveResult {
  text: string;
  confidence: number;
  elapsed_ms: number;
  method: string;
  variant: string;
  success: boolean;
}

export interface ImageRecognition {
  challenge_type: string;
  supported: boolean;
  reason: string;
  width: number;
  height: number;
}

export interface BatchResult {
  count: number;
  correct: number;
  accuracy: number;
  avg_time_ms: number;
  results: {
    truth: string;
    predicted: string;
    confidence: number;
    correct: boolean;
  }[];
}

export interface VerificationResult {
  provider: string;
  verified: boolean;
  status: string;
  message: string;
  error_codes: string[];
  token_fingerprint: string;
}

export interface ProviderRecognition {
  provider: string;
  invisible: boolean;
  matched_signals: string[];
  supported: boolean;
  verification_supported: boolean;
}

export interface Stats {
  total_attempts: number;
  successful: number;
  failed: number;
  accuracy: number;
  avg_time_ms: number;
  total_cost_usd: number;
  by_method: Record<string, number>;
  recent: Record<string, unknown>[];
}

export type Provider = "recaptcha" | "hcaptcha" | "turnstile";

async function asJson<T>(res: Response): Promise<T> {
  const data = await res.json();
  if (!res.ok) {
    // Surface backend error messages (e.g. Tesseract missing -> 503).
    const msg = (data && (data.error || data.detail)) || res.statusText;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data as T;
}

export const api = {
  config: () => fetch("/api/config").then((r) => asJson<Config>(r)),

  stats: () => fetch("/api/stats").then((r) => asJson<Stats>(r)),

  resetStats: () =>
    fetch("/api/stats/reset", { method: "POST" }).then((r) => asJson(r)),

  // Returns the PNG blob URL plus the ground-truth label from the header.
  async sample(): Promise<{ url: string; label: string }> {
    const res = await fetch("/api/sample");
    if (!res.ok) throw new Error("Could not fetch sample");
    const label = res.headers.get("X-Captcha-Label") || "?";
    const blob = await res.blob();
    return { url: URL.createObjectURL(blob), label };
  },

  solveSample: () =>
    fetch("/api/solve/sample", { method: "POST" }).then((r) =>
      asJson<{
        ground_truth: string;
        image_base64: string;
        solve: SolveResult;
        correct: boolean;
      }>(r)
    ),

  async solveUpload(file: File, expectedLength: number) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("expected_length", String(expectedLength));
    return fetch("/api/solve", { method: "POST", body: fd }).then((r) =>
      asJson<{ recognition: ImageRecognition; solve: SolveResult }>(r)
    );
  },

  recognizeProvider(html: string) {
    const fd = new FormData();
    fd.append("html", html);
    return fetch("/api/recognize/provider", { method: "POST", body: fd }).then(
      (r) => asJson<ProviderRecognition>(r)
    );
  },

  verify(provider: Provider, token: string) {
    const fd = new FormData();
    fd.append("provider", provider);
    fd.append("token", token);
    return fetch("/api/verify", { method: "POST", body: fd }).then((r) =>
      asJson<VerificationResult>(r)
    );
  },

  batch(count: number) {
    const fd = new FormData();
    fd.append("count", String(count));
    return fetch("/api/batch", { method: "POST", body: fd }).then((r) =>
      asJson<BatchResult>(r)
    );
  },
};
