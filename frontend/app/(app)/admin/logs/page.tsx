"use client";

import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { Button } from "@/components/ui/button";

type LogItem = {
  conversion_id: string;
  user_id: string;
  level: string;
  message: string;
  created_at: string;
};

export default function AdminLogs() {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // Pagination
  const [offset, setOffset] = useState(0);
  const limit = 15;

  async function loadLogs(currentSearch = search, currentLevel = levelFilter, currentOffset = offset) {
    setLoading(true);
    setError("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      const data = await client.getAdminLogs(
        currentLevel || undefined,
        currentSearch || undefined,
        limit,
        currentOffset
      );
      setLogs(data.items);
    } catch (err: any) {
      setError(err?.message || "Failed to load system logs.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLogs(search, levelFilter, offset);
  }, [offset, levelFilter]);

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setOffset(0);
    loadLogs(search, levelFilter, 0);
  }

  return (
    <section className="page-panel" style={{ animation: "fadeInSlideUp 0.3s var(--ease-out-quart) forwards" }}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Admin Portal</p>
          <h1>System Logs</h1>
        </div>
      </div>

      <div style={{ display: "flex", gap: "16px", margin: "20px 0", flexWrap: "wrap" }}>
        <form onSubmit={handleSearchSubmit} style={{ flex: 1, display: "flex", gap: "8px" }}>
          <div style={{ flex: 1, position: "relative" }}>
            <Search size={16} style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input 
              type="text" 
              placeholder="Search logs by message or conversion ID..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: "100%",
                height: "40px",
                padding: "0 12px 0 36px",
                borderRadius: "6px",
                border: "1px solid var(--border)",
                background: "var(--surface)",
                color: "var(--text)",
              }}
            />
          </div>
          <Button type="submit">Search</Button>
        </form>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <label style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Level:</label>
          <select 
            value={levelFilter} 
            onChange={(e) => { setLevelFilter(e.target.value); setOffset(0); }}
            style={{
              height: "40px",
              padding: "0 12px",
              borderRadius: "6px",
              border: "1px solid var(--border)",
              background: "var(--surface)",
              color: "var(--text)",
            }}
          >
            <option value="">All Levels</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
        </div>
      </div>

      {error ? <p className="message error-message">{error}</p> : null}

      {loading ? (
        <div className="skeleton-list" style={{ height: "300px" }} />
      ) : (
        <div className="table-responsive" style={{ overflowX: "auto", margin: "16px 0" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)", paddingBottom: "10px" }}>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Time</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Level</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Conversion ID</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>User ID</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Message</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid var(--border)", height: "48px" }}>
                  <td style={{ padding: "12px", fontSize: "var(--text-sm)", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: "12px" }}>
                    <span 
                      style={{ 
                        fontSize: "var(--text-xs)",
                        fontWeight: 650,
                        padding: "2px 6px",
                        borderRadius: "4px",
                        textTransform: "uppercase",
                        background: log.level === "error" ? "rgba(198, 40, 40, 0.1)" : log.level === "warning" ? "rgba(239, 108, 0, 0.1)" : "rgba(33, 150, 243, 0.1)",
                        color: log.level === "error" ? "var(--error)" : log.level === "warning" ? "var(--warning)" : "var(--primary)",
                        border: "1px solid color-mix(in oklch, var(--border) 50%, transparent)"
                      }}
                    >
                      {log.level}
                    </span>
                  </td>
                  <td style={{ padding: "12px", fontSize: "var(--text-xs)", fontFamily: "monospace" }}>
                    {log.conversion_id.slice(0, 8)}...
                  </td>
                  <td style={{ padding: "12px", fontSize: "var(--text-xs)", fontFamily: "monospace" }}>
                    {log.user_id.slice(0, 8)}...
                  </td>
                  <td style={{ padding: "12px", fontSize: "var(--text-sm)", fontWeight: 500 }}>
                    {log.message}
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
                    No system logs found matching the criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "20px" }}>
        <Button 
          variant="secondary"
          disabled={offset === 0} 
          onClick={() => setOffset(Math.max(0, offset - limit))}
          style={{ minHeight: "36px", padding: "0 16px" }}
        >
          Previous
        </Button>
        <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
          Page {Math.floor(offset / limit) + 1}
        </span>
        <Button 
          variant="secondary"
          disabled={logs.length < limit} 
          onClick={() => setOffset(offset + limit)}
          style={{ minHeight: "36px", padding: "0 16px" }}
        >
          Next
        </Button>
      </div>
    </section>
  );
}
