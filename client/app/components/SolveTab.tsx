"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { ImageRecognition, SolveResult } from "../lib/api";

function ResultPanel({
  solve,
  correct,
  groundTruth,
}: {
  solve: SolveResult;
  correct?: boolean;
  groundTruth?: string;
}) {
  const badgeText =
    correct === undefined
      ? solve.success
        ? "Text read"
        : "No text found"
      : correct
        ? "Correct"
        : "Incorrect";
  const badgeClass =
    correct === undefined ? (solve.success ? "ok" : "bad") : correct ? "ok" : "bad";

  return (
    <div className="result-panel">
      <div className="result-head">
        <h3>OCR result</h3>
        <span className={`badge ${badgeClass}`}>{badgeText}</span>
      </div>
      <p className="prediction">{solve.text || "No text detected"}</p>
      <div className="result-grid">
        {groundTruth !== undefined && (
          <div className="result-item"><span>Expected answer</span><strong>{groundTruth}</strong></div>
        )}
        <div className="result-item"><span>Confidence</span><strong>{(solve.confidence * 100).toFixed(1)}%</strong></div>
        <div className="result-item"><span>Processing time</span><strong>{solve.elapsed_ms} ms</strong></div>
        <div className="result-item"><span>Method</span><strong>{solve.method}</strong></div>
      </div>
    </div>
  );
}

export default function SolveTab() {
  const [sample, setSample] = useState<{ url: string; label: string } | null>(
    null
  );
  const [sampleResult, setSampleResult] = useState<{
    solve: SolveResult;
    correct: boolean;
    ground_truth: string;
  } | null>(null);
  const [sampleError, setSampleError] = useState("");
  const [uploadResult, setUploadResult] = useState<{
    recognition: ImageRecognition;
    solve: SolveResult;
  } | null>(null);
  const [uploadError, setUploadError] = useState("");
  const [expLen, setExpLen] = useState(5);
  const [file, setFile] = useState<File | null>(null);
  const [uploadPreview, setUploadPreview] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!file) {
      setUploadPreview("");
      return;
    }
    const url = URL.createObjectURL(file);
    setUploadPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  async function loadSample() {
    setSampleError("");
    setSampleResult(null);
    try {
      const next = await api.sample();
      setSample((current) => {
        if (current?.url.startsWith("blob:")) URL.revokeObjectURL(current.url);
        return next;
      });
    } catch (e) {
      setSampleError((e as Error).message);
    }
  }
  useEffect(() => {
    loadSample();
  }, []);

  async function solveSample() {
    setBusy(true);
    setSampleError("");
    try {
      const d = await api.solveSample();
      setSample((current) => {
        if (current?.url.startsWith("blob:")) URL.revokeObjectURL(current.url);
        return {
          url: `data:image/png;base64,${d.image_base64}`,
          label: d.ground_truth,
        };
      });
      setSampleResult(d);
    } catch (e) {
      setSampleError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function solveUpload() {
    if (!file) {
      setUploadError("Choose an image first.");
      return;
    }
    setBusy(true);
    setUploadError("");
    try {
      const d = await api.solveUpload(file, expLen);
      setUploadResult(d);
    } catch (e) {
      setUploadResult(null);
      setUploadError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="card">
        <h2>Try a synthetic CAPTCHA</h2>
        <p className="hint">
          Generates a CAPTCHA we own, runs our custom OCR engine, and compares
          to the known answer.
        </p>
        <div className="row">
          <button className="go secondary" onClick={loadSample} disabled={busy}>
            Get a sample
          </button>
          <button className="go" onClick={solveSample} disabled={busy}>
            {busy ? "Solving…" : "Generate & solve"}
          </button>
        </div>
        {sample && (
          <div className="image-preview" style={{ marginTop: 14 }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img className="captcha" src={sample.url} alt="captcha sample" />
            <span className="muted">Known answer: <b>{sample.label}</b></span>
          </div>
        )}
        {sampleError && <div className="banner" role="alert">{sampleError}</div>}
        {sampleResult && (
          <ResultPanel
            solve={sampleResult.solve}
            correct={sampleResult.correct}
            groundTruth={sampleResult.ground_truth}
          />
        )}
      </div>

      <div className="card">
        <h2>Upload your own image</h2>
        <p className="hint">
          Recognizes the challenge type first; solves it only if it is a
          supported text CAPTCHA.
        </p>
        <div className="row">
          <label className="field-label">
            CAPTCHA image
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setUploadResult(null);
                setUploadError("");
              }}
            />
          </label>
          <label className="field-label compact-field">
            Expected text length
            <input
              type="number"
              min={1}
              max={12}
              value={expLen}
              onChange={(e) => setExpLen(Number(e.target.value))}
            />
          </label>
          <button className="go" onClick={solveUpload} disabled={busy}>
            {busy ? "Reading image…" : "Recognize & solve"}
          </button>
        </div>
        {uploadPreview && file && (
          <div className="image-preview" style={{ marginTop: 14 }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className="captcha"
              src={uploadPreview}
              alt="Uploaded CAPTCHA image preview"
            />
            <span className="muted">{file.name}</span>
          </div>
        )}
        {uploadError && <div className="banner" role="alert">{uploadError}</div>}
        {uploadResult && (
          <>
            <div className="recognition-note">
              <b>Image check:</b> {uploadResult.recognition.challenge_type} challenge
              ({uploadResult.recognition.width} × {uploadResult.recognition.height} px). {uploadResult.recognition.reason}
            </div>
            <ResultPanel solve={uploadResult.solve} />
          </>
        )}
      </div>
    </>
  );
}
