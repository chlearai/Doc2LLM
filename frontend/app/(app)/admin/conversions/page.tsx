"use client";

import { useEffect, useState } from "react";
import { Search, XOctagon, RefreshCw } from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { Button } from "@/components/ui/button";
import type { Conversion } from "@/lib/types";

export default function AdminConversions() {
  const [conversions, setConversions] = useState<Conversion[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  
  // Pagination
  const [offset, setOffset] = useState(0);
  const limit = 10;

  function getOwnerLabel(conversion: Conversion) {
    return conversion.user_full_name?.trim() || conversion.user_email || conversion.user_id || "Unknown user";
  }

  async function loadConversions(currentSearch = search, currentStatus = statusFilter, currentOffset = offset) {
    setLoading(true);
    setError("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      const data = await client.listAdminConversions({
        search: currentSearch || undefined,
        status: currentStatus || undefined,
        limit,
        offset: currentOffset,
      });
      // Show all jobs including deleted/failed for comprehensive audit
      setConversions(data.items);
    } catch (err: any) {
      setError(err?.message || "Failed to load conversions list.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadConversions(search, statusFilter, offset);
  }, [offset, statusFilter]);

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setOffset(0);
    loadConversions(search, statusFilter, 0);
  }

  async function handleCancelJob(id: string) {
    if (!confirm("Are you sure you want to cancel this conversion job?")) return;
    setError("");
    setNotice("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      await client.cancelAdminConversion(id);
      setNotice("Job successfully cancelled.");
      loadConversions(search, statusFilter, offset);
    } catch (err: any) {
      setError(err?.message || "Failed to cancel job.");
    }
  }

  async function handleRetryJob(id: string) {
    setError("");
    setNotice("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      await client.retryAdminConversion(id);
      setNotice("Simulated retry initiated. Status updated.");
      loadConversions(search, statusFilter, offset);
    } catch (err: any) {
      setError(err?.message || "Failed to retry job.");
    }
  }

  return (
    <section className="page-panel" style={{ animation: "fadeInSlideUp 0.3s var(--ease-out-quart) forwards" }}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Admin Portal</p>
          <h1>Conversion Jobs</h1>
        </div>
      </div>

      <div style={{ display: "flex", gap: "16px", margin: "20px 0", flexWrap: "wrap" }}>
        <form onSubmit={handleSearchSubmit} style={{ flex: 1, display: "flex", gap: "8px" }}>
          <div style={{ flex: 1, position: "relative" }}>
            <Search size={16} style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input 
              type="text" 
              placeholder="Search file name..." 
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
          <label style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Status:</label>
          <select 
            value={statusFilter} 
            onChange={(e) => { setStatusFilter(e.target.value); setOffset(0); }}
            style={{
              height: "40px",
              padding: "0 12px",
              borderRadius: "6px",
              border: "1px solid var(--border)",
              background: "var(--surface)",
              color: "var(--text)",
            }}
          >
            <option value="">All Statuses</option>
            <option value="UPLOAD_RECEIVED">Upload Received</option>
            <option value="PENDING">Pending</option>
            <option value="PROCESSING">Processing</option>
            <option value="COMPLETED">Completed</option>
            <option value="FAILED">Failed</option>
            <option value="DELETED">Deleted</option>
          </select>
        </div>
      </div>

      {error ? <p className="message error-message">{error}</p> : null}
      {notice ? <p className="message success-message">{notice}</p> : null}

      {loading ? (
        <div className="skeleton-list" style={{ height: "300px" }} />
      ) : (
        <div className="table-responsive" style={{ overflowX: "auto", margin: "16px 0" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)", paddingBottom: "10px" }}>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Job ID</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>File details</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Status</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Timing</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Error Message</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {conversions.map((conv) => (
                <tr key={conv.id} style={{ borderBottom: "1px solid var(--border)", height: "60px" }}>
                  <td style={{ padding: "12px", fontSize: "var(--text-xs)", fontFamily: "monospace" }}>{conv.id.slice(0, 8)}...</td>
                  <td style={{ padding: "12px" }}>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontWeight: 600 }}>{conv.original_file_name}</span>
                      <span style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>User: {getOwnerLabel(conv)}</span>
                    </div>
                  </td>
                  <td style={{ padding: "12px" }}>
                    <span 
                      style={{ 
                        fontSize: "var(--text-xs)",
                        fontWeight: 600,
                        padding: "4px 8px",
                        borderRadius: "12px",
                        background: conv.status === "COMPLETED" ? "rgba(46, 125, 50, 0.1)" : conv.status === "FAILED" ? "rgba(198, 40, 40, 0.1)" : "var(--background)",
                        border: "1px solid var(--border)",
                        color: conv.status === "COMPLETED" ? "var(--success)" : conv.status === "FAILED" ? "var(--error)" : "var(--text-muted)"
                      }}
                    >
                      {conv.status}
                    </span>
                  </td>
                  <td style={{ padding: "12px", fontSize: "var(--text-xs)", color: "var(--text-muted)", lineHeight: "1.4" }}>
                    <div>Created: {new Date(conv.created_at).toLocaleTimeString()}</div>
                    {conv.completed_at && <div>Finished: {new Date(conv.completed_at).toLocaleTimeString()}</div>}
                  </td>
                  <td style={{ padding: "12px", fontSize: "var(--text-sm)", color: "var(--error)", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {conv.error_message || "-"}
                  </td>
                  <td style={{ padding: "12px", textAlign: "right" }}>
                    <div style={{ display: "inline-flex", gap: "8px" }}>
                      {(conv.status === "UPLOAD_RECEIVED" || conv.status === "PENDING" || conv.status === "PROCESSING") && (
                        <Button 
                          type="button" 
                          variant="secondary"
                          onClick={() => handleCancelJob(conv.id)}
                          style={{ padding: "4px 10px", fontSize: "0.8rem", height: "32px", color: "var(--error)" }}
                          icon={<XOctagon size={14} />}
                        >
                          Cancel
                        </Button>
                      )}
                      {conv.status === "FAILED" && (
                        <Button 
                          type="button" 
                          variant="secondary"
                          onClick={() => handleRetryJob(conv.id)}
                          style={{ padding: "4px 10px", fontSize: "0.8rem", height: "32px" }}
                          icon={<RefreshCw size={14} />}
                        >
                          Retry
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {conversions.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
                    No conversion jobs found matching the criteria.
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
          disabled={conversions.length < limit} 
          onClick={() => setOffset(offset + limit)}
          style={{ minHeight: "36px", padding: "0 16px" }}
        >
          Next
        </Button>
      </div>
    </section>
  );
}
