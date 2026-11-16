"use client";

import { useEffect, useState } from "react";
import { api, Config } from "./lib/api";
import SolveTab from "./components/SolveTab";
import ProviderTab from "./components/ProviderTab";
import VerifyTab from "./components/VerifyTab";
import StatsTab from "./components/StatsTab";

type TabId = "solve" | "provider" | "verify" | "stats";

const TABS: { id: TabId; number: string; label: string; title: string; description: string }[] = [
  {
    id: "solve",
    number: "01",
    label: "Recognize & Solve",
    title: "Recognize and solve a text challenge",
    description: "Generate a controlled sample or upload an image to see how the recognition and OCR pipeline handles it.",
  },
  {
    id: "provider",
    number: "02",
    label: "Provider Recognition",
    title: "Identify a CAPTCHA provider",
    description: "Check HTML from an owned test page, or run a built-in example for reCAPTCHA, hCaptcha, or Turnstile.",
  },
  {
    id: "verify",
    number: "03",
    label: "Token Verification",
    title: "Verify provider test tokens",
    description: "Complete an official test widget and follow its token through server-side verification.",
  },
  {
    id: "stats",
    number: "04",
    label: "Batch & Dashboard",
    title: "Measure OCR performance",
    description: "Run a batch of controlled samples, compare readings with known answers, and review session totals.",
  },
];

export default function Page() {
  const [tab, setTab] = useState<TabId>("solve");
  const [config, setConfig] = useState<Config | null>(null);
  const [backendError, setBackendError] = useState<string>("");
  const activeTab = TABS.find((item) => item.id === tab)!;

  useEffect(() => {
    api
      .config()
      .then(setConfig)
      .catch(() =>
        setBackendError(
          "Cannot reach the FastAPI backend on port 8000. Start it with: " +
            "cd server && source .venv/bin/activate && uvicorn app.main:app --reload"
        )
      );
  }, []);

  return (
    <>
      {backendError && <div className="banner" role="alert">{backendError}</div>}

      <nav className="tabs" role="tablist" aria-label="Project features">
        {TABS.map((t) => (
          <button
            key={t.id}
            id={`tab-${t.id}`}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            aria-controls={`panel-${t.id}`}
            className={tab === t.id ? "active" : ""}
            onClick={() => setTab(t.id)}
          >
            <span className="tab-number" aria-hidden="true">{t.number}</span>
            <span>{t.label}</span>
          </button>
        ))}
      </nav>

      <section
        id={`panel-${tab}`}
        role="tabpanel"
        aria-labelledby={`tab-${tab}`}
        tabIndex={0}
      >
        <div className="page-intro">
          <p className="eyebrow">Project workspace · {activeTab.number} of 04</p>
          <h2>{activeTab.title}</h2>
          <p>{activeTab.description}</p>
        </div>
        {tab === "solve" && <SolveTab />}
        {tab === "provider" && <ProviderTab />}
        {tab === "verify" && <VerifyTab config={config} />}
        {tab === "stats" && <StatsTab />}
      </section>
    </>
  );
}
