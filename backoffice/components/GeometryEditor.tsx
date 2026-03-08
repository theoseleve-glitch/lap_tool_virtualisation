"use client";

import { useState } from "react";

type DraftState = { boundary_polygon_wkt: string; centerline_wkt: string; start_finish_wkt: string; audit_note: string };

export function GeometryEditor({ layoutVersionId }: { layoutVersionId: string }) {
  const [undoStack, setUndoStack] = useState<DraftState[]>([]);
  const [draft, setDraft] = useState<DraftState>({
    boundary_polygon_wkt: "POLYGON((0 0,1 0,1 1,0 1,0 0))",
    centerline_wkt: "LINESTRING(0 0,1 1)",
    start_finish_wkt: "POINT(0 0)",
    audit_note: "manual correction",
  });

  function update(next: Partial<DraftState>) {
    setUndoStack((s) => [...s, draft]);
    setDraft({ ...draft, ...next });
  }

  function undo() {
    const previous = undoStack.at(-1);
    if (!previous) return;
    setUndoStack((s) => s.slice(0, -1));
    setDraft(previous);
  }

  async function save(submit_for_review: boolean) {
    await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/v1/layouts/${layoutVersionId}/geometry-edits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...draft, sectors: {}, submit_for_review }),
    });
  }

  return (
    <section>
      <h3>Geometry Editing</h3>
      <button onClick={undo} disabled={!undoStack.length}>Undo</button>
      <textarea value={draft.boundary_polygon_wkt} onChange={(e) => update({ boundary_polygon_wkt: e.target.value })} />
      <textarea value={draft.centerline_wkt} onChange={(e) => update({ centerline_wkt: e.target.value })} />
      <textarea value={draft.start_finish_wkt} onChange={(e) => update({ start_finish_wkt: e.target.value })} />
      <textarea value={draft.audit_note} onChange={(e) => update({ audit_note: e.target.value })} />
      <button onClick={() => save(false)}>Save draft</button>
      <button onClick={() => save(true)}>Submit for review</button>
    </section>
  );
}
