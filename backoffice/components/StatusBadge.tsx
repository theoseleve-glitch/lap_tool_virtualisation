export function StatusBadge({ value }: { value: string }) {
  const color = value.includes("fail") || value.includes("reject") ? "#7f1d1d" : "#14532d";
  return <span style={{ background: color, color: "white", padding: "2px 8px", borderRadius: 6 }}>{value}</span>;
}
