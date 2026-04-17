import type { Stats } from "@/lib/api";

export default function StatsBar({ stats }: { stats: Stats | null }) {
  if (!stats) return null;
  return (
    <div className="data-bar">
      <div className="container" style={{ display: "flex", gap: "24px", overflowX: "auto" }}>
        <span><strong>{stats.total_stories?.toLocaleString() ?? "—"}</strong> stories tracked</span>
        <span style={{ color: "var(--border-strong)" }}>|</span>
        <span>Updates every <strong>10 minutes</strong></span>
        <span style={{ color: "var(--border-strong)" }}>|</span>
        <span>Algorithm: <strong>Multi-source validation</strong></span>
        {stats.latest_update && (
          <>
            <span style={{ color: "var(--border-strong)" }}>|</span>
            <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--brand-primary)" }} />
              Latest sync: {stats.latest_update}
            </span>
          </>
        )}
      </div>
    </div>
  );
}
