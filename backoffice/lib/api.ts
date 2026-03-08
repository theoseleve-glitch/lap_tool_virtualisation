export type LayoutVersion = {
  id: string;
  layout_id: string;
  version: number;
  status: string;
  review_status: string;
};

export async function fetchLayouts(): Promise<LayoutVersion[]> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/v1/layouts`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch layouts");
  return res.json();
}
