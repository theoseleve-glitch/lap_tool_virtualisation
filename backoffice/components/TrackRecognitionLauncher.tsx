"use client";

import { CSSProperties, FormEvent, useState } from "react";

type LaunchResponse = {
  output_dir: string;
  run_id: string;
  pipeline_version: string;
  counts: Record<string, number>;
};

const cardStyle: CSSProperties = {
  maxWidth: 760,
  margin: "2rem auto",
  padding: "1.5rem",
  border: "1px solid #e5e7eb",
  borderRadius: 12,
  background: "#fff",
  boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
};

const inputStyle: CSSProperties = {
  width: "100%",
  padding: "0.6rem 0.75rem",
  border: "1px solid #d1d5db",
  borderRadius: 8,
  marginTop: "0.3rem",
};

export function TrackRecognitionLauncher() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LaunchResponse | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData(event.currentTarget);
    const payload = {
      output_root: String(formData.get("output_root") || "outputs"),
      auto_merge_threshold: Number(formData.get("auto_merge_threshold") || 0.85),
      suggest_merge_threshold: Number(formData.get("suggest_merge_threshold") || 0.6),
      uk_include_ni_from_official_flow: formData.get("uk_include_ni_from_official_flow") === "on",
    };

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/v1/tool/launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Launch failed (${response.status})`);
      }

      const data = (await response.json()) as LaunchResponse;
      setResult(data);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ background: "#f8fafc", minHeight: "100vh", padding: "1rem" }}>
      <form onSubmit={onSubmit} style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>Track Recognition Launcher</h1>
        <p style={{ color: "#4b5563" }}>
          Launch the recognition pipeline locally, choose where outputs are written, and tune optional layout recognition behavior.
        </p>

        <label>
          Output folder
          <input name="output_root" defaultValue="outputs" required style={inputStyle} />
        </label>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
          <label>
            Auto-merge threshold
            <input name="auto_merge_threshold" type="number" min="0" max="1" step="0.01" defaultValue="0.85" style={inputStyle} />
          </label>

          <label>
            Suggest-merge threshold
            <input name="suggest_merge_threshold" type="number" min="0" max="1" step="0.01" defaultValue="0.6" style={inputStyle} />
          </label>
        </div>

        <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 14 }}>
          <input name="uk_include_ni_from_official_flow" type="checkbox" defaultChecked />
          Include Northern Ireland from official UK source flow
        </label>

        <button
          type="submit"
          disabled={loading}
          style={{ marginTop: 16, padding: "0.7rem 1rem", borderRadius: 8, border: "none", background: "#111827", color: "white" }}
        >
          {loading ? "Launching..." : "Launch recognition tool"}
        </button>

        {error ? <p style={{ color: "#b91c1c" }}>{error}</p> : null}

        {result ? (
          <div style={{ marginTop: 16, padding: "0.9rem", borderRadius: 8, background: "#f3f4f6" }}>
            <strong>Run launched successfully</strong>
            <p>Run ID: {result.run_id}</p>
            <p>Output directory: {result.output_dir}</p>
            <p>
              Counts — Evidence: {result.counts.evidence}, Candidates: {result.counts.candidates}, Accepted: {result.counts.accepted},
              Review: {result.counts.review}, Rejected: {result.counts.rejected}
            </p>
          </div>
        ) : null}
      </form>
    </main>
  );
}
