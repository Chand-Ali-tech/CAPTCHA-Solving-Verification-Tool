"use client";

import { useCallback, useState } from "react";
import CaptchaWidget from "./CaptchaWidget";
import { api, Config, Provider, VerificationResult } from "../lib/api";

function StatusLine({ r }: { r: VerificationResult | string | null }) {
  if (!r) return <span className="muted">Waiting for token…</span>;
  if (typeof r === "string") return <span className="muted">{r}</span>;
  return (
    <span>
      <span className={"badge " + (r.verified ? "ok" : "bad")}>
        {r.verified ? "VERIFIED" : r.status.toUpperCase()}
      </span>{" "}
      {r.message}
      {r.token_fingerprint && (
        <span className="muted"> (token #{r.token_fingerprint})</span>
      )}
    </span>
  );
}

export default function VerifyTab({ config }: { config: Config | null }) {
  const keys = config?.site_keys;
  const [status, setStatus] = useState<
    Record<Provider, VerificationResult | string | null>
  >({ recaptcha: null, hcaptcha: null, turnstile: null });

  const verifyToken = useCallback(async (provider: Provider, token: string) => {
    setStatus((s) => ({ ...s, [provider]: "verifying…" }));
    try {
      const r = await api.verify(provider, token);
      setStatus((s) => ({ ...s, [provider]: r }));
    } catch (e) {
      setStatus((s) => ({ ...s, [provider]: "Error: " + (e as Error).message }));
    }
  }, []);

  // Failure-case tester
  const [failProvider, setFailProvider] = useState<Provider>("recaptcha");
  const [failToken, setFailToken] = useState("");
  const [failOut, setFailOut] = useState("");

  async function runFail(token: string) {
    try {
      setFailOut(
        JSON.stringify(await api.verify(failProvider, token), null, 2)
      );
    } catch (e) {
      setFailOut("Error: " + (e as Error).message);
    }
  }

  const widgets: { provider: Provider; label: string }[] = [
    { provider: "recaptcha", label: "Google reCAPTCHA v2" },
    { provider: "hcaptcha", label: "hCaptcha" },
    { provider: "turnstile", label: "Cloudflare Turnstile" },
  ];

  return (
    <>
      <div className="card">
        <h2>Official token verification</h2>
        <p className="hint">
          These are each provider&apos;s official <b>test</b> widgets (always
          pass). Solve one, then we verify its token server-side with the secret
          key. The raw token never leaves the server exposed — only a short
          fingerprint is shown.
        </p>
        {widgets.map((w) => (
          <div className="widget-block" key={w.provider}>
            <h3>{w.label}</h3>
            <CaptchaWidget
              provider={w.provider}
              sitekey={keys?.[w.provider] ?? ""}
              onToken={(t) => verifyToken(w.provider, t)}
              onError={(m) =>
                setStatus((s) => ({ ...s, [w.provider]: "Error: " + m }))
              }
            />
            <div className="widget-status">
              <StatusLine r={status[w.provider]} />
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h2>Failure-case testing</h2>
        <p className="hint">
          Verify handling of missing / invalid / expired / reused tokens.
        </p>
        <div className="row">
          <select
            value={failProvider}
            onChange={(e) => setFailProvider(e.target.value as Provider)}
          >
            <option value="recaptcha">reCAPTCHA</option>
            <option value="hcaptcha">hCaptcha</option>
            <option value="turnstile">Turnstile</option>
          </select>
          <input
            value={failToken}
            onChange={(e) => setFailToken(e.target.value)}
            aria-label="Verification token for failure test"
            placeholder="Token (leave blank to test missing token)"
            style={{ flex: 1, minWidth: 230 }}
          />
          <button className="go" onClick={() => runFail(failToken)}>
            Verify
          </button>
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          <button className="go secondary" onClick={() => runFail("")}>
            Test: missing
          </button>
          <button
            className="go secondary"
            onClick={() => runFail("this-is-not-a-real-token")}
          >
            Test: invalid
          </button>
        </div>
        {failOut && <pre style={{ marginTop: 12 }}>{failOut}</pre>}
      </div>
    </>
  );
}
