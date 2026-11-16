"use client";

import { useState } from "react";
import { api } from "../lib/api";
import type { ProviderRecognition } from "../lib/api";

const EXAMPLES = {
  recaptcha:
    '<script src="https://www.google.com/recaptcha/api.js"></script>\n<div class="g-recaptcha" data-sitekey="XXX"></div>',
  turnstile:
    '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>\n<div class="cf-turnstile" data-sitekey="XXX"></div>',
  hcaptcha:
    '<script src="https://js.hcaptcha.com/1/api.js"></script>\n<div class="h-captcha" data-sitekey="XXX"></div>',
  cloudflare_challenge:
    '<script src="/cdn-cgi/challenge-platform/chl.js"></script>\n<div id="challenge-error-text">Verification failed</div>\n<a href="https://www.cloudflare.com/">Cloudflare</a>',
};

const PROVIDER_LABELS: Record<string, string> = {
  recaptcha: "Google reCAPTCHA",
  hcaptcha: "hCaptcha",
  turnstile: "Cloudflare Turnstile",
  cloudflare_challenge: "Cloudflare managed challenge page",
  multiple: "Multiple provider signatures",
  none: "No supported provider detected",
};

export default function ProviderTab() {
  const [html, setHtml] = useState("");
  const [result, setResult] = useState<ProviderRecognition | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function detect(source = html) {
    setBusy(true);
    setError("");
    try {
      setHtml(source);
      setResult(await api.recognizeProvider(source));
    } catch (e) {
      setResult(null);
      setError("Error: " + (e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h2>Detect the provider from page HTML</h2>
      <p className="hint">
        Paste the HTML of an owned test page or an official provider demo. We
        identify reCAPTCHA, hCaptcha, and Turnstile widgets, plus Cloudflare
        managed challenge pages.
      </p>
      <textarea
        value={html}
        onChange={(e) => setHtml(e.target.value)}
        placeholder={'e.g.  <div class="g-recaptcha" data-sitekey="..."></div>'}
      />
      <div className="row" style={{ marginTop: 10 }}>
        <button className="go" onClick={() => detect()} disabled={busy}>
          {busy ? "Detecting…" : "Detect provider"}
        </button>
        <button
          className="go secondary"
          onClick={() => detect(EXAMPLES.recaptcha)}
          disabled={busy}
        >
          Test reCAPTCHA
        </button>
        <button
          className="go secondary"
          onClick={() => detect(EXAMPLES.turnstile)}
          disabled={busy}
        >
          Test Turnstile
        </button>
        <button
          className="go secondary"
          onClick={() => detect(EXAMPLES.hcaptcha)}
          disabled={busy}
        >
          Test hCaptcha
        </button>
        <button
          className="go secondary"
          onClick={() => detect(EXAMPLES.cloudflare_challenge)}
          disabled={busy}
        >
          Test Cloudflare challenge page
        </button>
      </div>
      {error && <pre style={{ marginTop: 12 }}>{error}</pre>}
      {result && (
        <div className="card" style={{ marginTop: 14 }}>
          <div className="result-head">
            <h3>{PROVIDER_LABELS[result.provider] ?? result.provider}</h3>
            <span className={`badge ${result.supported ? "ok" : "bad"}`}>
              {result.supported ? "Recognized" : "No match"}
            </span>
          </div>
          <p>
            Token verification: <b>{result.verification_supported ? "supported" : "not supported for this result"}</b>
          </p>
          {result.invisible && <p>reCAPTCHA mode: invisible</p>}
          {result.matched_signals.length > 0 && (
            <details className="signature-list">
              <summary>View {result.matched_signals.length} matched HTML signatures</summary>
              <ul>
                {result.matched_signals.map((signal) => (
                  <li key={signal}><code>{signal}</code></li>
                ))}
              </ul>
            </details>
          )}
          {result.provider === "cloudflare_challenge" && (
            <p className="hint">
              This is a Cloudflare-managed challenge page, not a Turnstile
              widget token flow.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
