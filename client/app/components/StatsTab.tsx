"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { BatchResult, Stats } from "../lib/api";

export default function StatsTab() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [batchResult, setBatchResult] = useState<BatchResult | null>(null);
  const [batchError, setBatchError] = useState("");
  const [count, setCount] = useState(20);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setStats(await api.stats());
    } catch {
      /* ignore transient fetch errors */
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function runBatch() {
    setBusy(true);
    setBatchError("");
    setBatchResult(null);
    try {
      const d = await api.batch(count);
      setBatchResult(d);
      refresh();
    } catch (e) {
      setBatchError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const tiles: [string, string | number][] = stats
    ? [
        ["Attempts", stats.total_attempts],
        ["Success", stats.successful],
        ["Failed", stats.failed],
        ["Accuracy", (stats.accuracy * 100).toFixed(1) + "%"],
        ["Avg time", stats.avg_time_ms + " ms"],
        ["Est. cost", "$" + stats.total_cost_usd.toFixed(4)],
      ]
    : [];

  return (
    <>
      <div className="card">
        <h2>Batch accuracy test</h2>
        <p className="hint">
          Generate N synthetic CAPTCHAs and solve them all for an accuracy
          measurement.
        </p>
        <div className="row">
          <label className="field-label compact-field">
            Number of samples
            <input
              type="number"
              min={1}
              max={200}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
            />
          </label>
          <button className="go" onClick={runBatch} disabled={busy}>
            {busy ? "Running…" : "Run batch"}
          </button>
        </div>
        {batchError && <div className="banner" role="alert">{batchError}</div>}
        {batchResult && (
          <>
            <div className="grid" style={{ marginTop: 16 }}>
              <div className="stat"><div className="n">{(batchResult.accuracy * 100).toFixed(1)}%</div><div className="l">Batch accuracy</div></div>
              <div className="stat"><div className="n">{batchResult.correct}/{batchResult.count}</div><div className="l">Correct readings</div></div>
              <div className="stat"><div className="n">{batchResult.avg_time_ms} ms</div><div className="l">Average time</div></div>
            </div>
            <div className="table-wrap" style={{ marginTop: 14 }}>
              <table className="data-table">
                <thead><tr><th>Expected</th><th>Predicted</th><th>Confidence</th><th>Result</th></tr></thead>
                <tbody>
                  {batchResult.results.map((row, index) => (
                    <tr key={`${row.truth}-${index}`}>
                      <td><code>{row.truth}</code></td>
                      <td><code>{row.predicted || "No text"}</code></td>
                      <td>{(row.confidence * 100).toFixed(0)}%</td>
                      <td><span className={`badge ${row.correct ? "ok" : "bad"}`}>{row.correct ? "Correct" : "Incorrect"}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      <div className="card">
        <h2>Live dashboard</h2>
        <p className="hint">Running totals for this backend session. Values reset when the backend restarts.</p>
        <div className="grid">
          {tiles.map(([label, n]) => (
            <div className="stat" key={label}>
              <div className="n">{n}</div>
              <div className="l">{label}</div>
            </div>
          ))}
        </div>
        <div className="row" style={{ marginTop: 12 }}>
          <button className="go" onClick={refresh}>
            Refresh
          </button>
          <button
            className="go secondary"
            onClick={async () => {
              await api.resetStats();
              refresh();
            }}
          >
            Reset
          </button>
        </div>
        {stats && (
          <>
            <h3>Attempts by method</h3>
            {Object.keys(stats.by_method).length ? (
              <div className="table-wrap">
                <table className="data-table">
                  <thead><tr><th>Method</th><th>Attempts</th></tr></thead>
                  <tbody>
                    {Object.entries(stats.by_method).map(([method, total]) => (
                      <tr key={method}><td>{method}</td><td>{total}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <p className="muted">No attempts recorded yet.</p>}
            <h3>Recent activity</h3>
            {stats.recent.length ? (
              <div className="table-wrap">
                <table className="data-table">
                  <thead><tr><th>Result</th><th>Method</th><th>Challenge</th><th>Time</th></tr></thead>
                  <tbody>
                    {stats.recent.slice(0, 10).map((event, index) => (
                      <tr key={`${String(event.method)}-${index}`}>
                        <td><span className={`badge ${event.success ? "ok" : "bad"}`}>{event.success ? "Success" : "Failed"}</span></td>
                        <td>{String(event.method ?? "—")}</td>
                        <td>{String(event.challenge_type ?? event.provider ?? "—")}</td>
                        <td>{String(event.elapsed_ms ?? 0)} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <p className="muted">Recent attempts will appear here.</p>}
            <details className="raw-data">
              <summary>View raw statistics response</summary>
              <pre>{JSON.stringify(stats, null, 2)}</pre>
            </details>
          </>
        )}
      </div>
    </>
  );
}
