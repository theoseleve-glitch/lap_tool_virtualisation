"use client";

import { useState } from "react";

export function ReviewActionPanel({ layoutVersionId }: { layoutVersionId: string }) {
  const [action, setAction] = useState("approve");
  const [notes, setNotes] = useState("");
  async function submit() {
    await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/v1/layouts/${layoutVersionId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, notes }),
    });
  }
  return (
    <section>
      <h3>Review Action Panel</h3>
      <select value={action} onChange={(e) => setAction(e.target.value)}>
        <option value="approve">approve</option>
        <option value="reject">reject</option>
        <option value="request_changes">request_changes</option>
      </select>
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="audit notes" />
      <button onClick={submit}>Submit review action</button>
    </section>
  );
}
