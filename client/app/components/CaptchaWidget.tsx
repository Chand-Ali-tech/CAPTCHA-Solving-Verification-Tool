"use client";

import { useEffect, useRef } from "react";
import type { Provider } from "../lib/api";

// Each provider exposes a global object with a .render(el, opts) method once
// its script has loaded with ?render=explicit.
const SCRIPTS: Record<Provider, string> = {
  recaptcha: "https://www.google.com/recaptcha/api.js?render=explicit",
  hcaptcha: "https://js.hcaptcha.com/1/api.js?render=explicit",
  turnstile:
    "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit",
};
const GLOBALS: Record<Provider, string> = {
  recaptcha: "grecaptcha",
  hcaptcha: "hcaptcha",
  turnstile: "turnstile",
};

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) return resolve();
    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.defer = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(s);
  });
}

// Poll until the provider's global (with a usable .render) is available.
function waitForGlobal(name: string, timeout = 10000): Promise<any> {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const tick = () => {
      const g = (window as any)[name];
      if (g && typeof g.render === "function") return resolve(g);
      if (Date.now() - start > timeout)
        return reject(new Error(`${name} did not load in time`));
      setTimeout(tick, 100);
    };
    tick();
  });
}

interface Props {
  provider: Provider;
  sitekey: string;
  onToken: (token: string) => void;
  onError?: (message: string) => void;
}

export default function CaptchaWidget({
  provider,
  sitekey,
  onToken,
  onError,
}: Props) {
  const boxRef = useRef<HTMLDivElement>(null);
  const rendered = useRef(false);
  // Keep the latest onToken without re-rendering the widget.
  const onTokenRef = useRef(onToken);
  onTokenRef.current = onToken;

  useEffect(() => {
    if (!sitekey || rendered.current) return;
    let active = true;
    (async () => {
      try {
        await loadScript(SCRIPTS[provider]);
        const g = await waitForGlobal(GLOBALS[provider]);
        if (!active || !boxRef.current || rendered.current) return;
        g.render(boxRef.current, {
          sitekey,
          callback: (token: string) => onTokenRef.current(token),
          "error-callback": () => onError?.("Widget reported an error."),
        });
        rendered.current = true;
      } catch (e) {
        onError?.((e as Error).message);
      }
    })();
    return () => {
      active = false;
    };
  }, [provider, sitekey, onError]);

  if (!sitekey) {
    return (
      <div className="muted">
        No site key configured for {provider}. Set it in the backend .env.
      </div>
    );
  }
  return <div ref={boxRef} />;
}
