"use client";

import { useEffect, useState } from "react";
import { Search, Download, Trash2, ExternalLink } from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { Button } from "@/components/ui/button";
import type { Conversion } from "@/lib/types";
import { formatFileSize } from "@/lib/format";

export default function AdminFiles() {
  const [files, setFiles] = useState<Conversion[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  
  // Pagination
  const [offset, setOffset] = useState(0);
  const limit = 10;

  async function loadFiles(currentSearch = search, currentStatus = statusFilter, currentOffset = offset) {
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
      // Filter out deleted from the list for better UX
      setFiles(data.items.filter((item) => item.status !== "DELETED"));
    } catch (err: any) {
      setError(err?.message || "Failed to load files list.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFiles(search, statusFilter, offset);
  }, [offset, statusFilter]);

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setOffset(0);
    loadFiles(search, statusFilter, 0);
  }

  async function handleDeleteFile(id: string) {
    if (!confirm("Are you sure you want to delete this conversion output and metadata permanently? This cannot be undone.")) return;
    setError("");
    setNotice("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      await client.deleteAdminConversion(id);
      setNotice("File and conversion metadata deleted successfully.");
      loadFiles(search, statusFilter, offset);
    } catch (err: any) {
      setError(err?.message || "Failed to delete file.");
    }
  }

  async function handleDownloadFile(file: Conversion) {
    setError("");
    setNotice("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      const res = await client.getDownloadUrl(file.id);
      window.open(res.download_url, "_blank");
      setNotice("Download link opened in new window.");
    } catch (err: any) {
      setError(err?.message || "Failed to fetch download link.");
    }
  }

  return (
    <section className="page-panel" style={{ animation: "fadeInSlideUp 0.3s var(--ease-out-quart) forwards" }}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Admin Portal</p>
          <h1>Converted Files</h1>
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
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>File Name</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Type</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Size</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Status</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Created</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => (
                <tr key={file.id} style={{ borderBottom: "1px solid var(--border)", height: "60px" }}>
                  <td style={{ padding: "12px" }}>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontWeight: 600 }}>{file.original_file_name}</span>
                      <span style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>Owner ID: {file.user_id || "System"}</span>
                    </div>
                  </td>
                  <td style={{ padding: "12px" }}>
                    <span 
                      style={{ 
                        fontSize: "var(--text-xs)",
                        fontWeight: 600,
                        padding: "2px 6px",
                        borderRadius: "4px",
                        background: "var(--surface-muted)",
                        border: "1px solid var(--border)",
                        textTransform: "uppercase"
                      }}
                    >
                      {file.file_type}
                    </span>
                  </td>
                  <td style={{ padding: "12px", fontSize: "var(--text-sm)" }}>{formatFileSize(file.file_size_bytes)}</td>
                  <td style={{ padding: "12px" }}>
                    <span 
                      style={{ 
                        fontSize: "var(--text-xs)",
                        fontWeight: 600,
                        padding: "4px 8px",
                        borderRadius: "12px",
                        background: file.status === "COMPLETED" ? "rgba(46, 125, 50, 0.1)" : file.status === "FAILED" ? "rgba(198, 40, 40, 0.1)" : "var(--background)",
                        border: "1px solid var(--border)",
                        color: file.status === "COMPLETED" ? "var(--success)" : file.status === "FAILED" ? "var(--error)" : "var(--text-muted)"
                      }}
                    >
                      {file.status}
                    </span>
                  </td>
                  <td style={{ padding: "12px", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {new Date(file.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: "12px", textAlign: "right" }}>
                    <div style={{ display: "inline-flex", gap: "8px" }}>
                      {file.status === "COMPLETED" && (
                        <Button 
                          type="button" 
                          variant="secondary"
                          onClick={() => handleDownloadFile(file)}
                          style={{ padding: "4px 10px", fontSize: "0.8rem", height: "32px" }}
                          icon={<Download size={14} />}
                        >
                          Download
                        </Button>
                      )}
                      <Button 
                        type="button" 
                        variant="secondary"
                        onClick={() => handleDeleteFile(file.id)}
                        style={{ padding: "4px 10px", fontSize: "0.8rem", height: "32px", color: "var(--error)" }}
                        icon={<Trash2 size={14} />}
                      >
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {files.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
                    No files found matching the criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "20px" }}>
        <button 
          disabled={offset === 0} 
          onClick={() => setOffset(Math.max(0, offset - limit))}
          className="btn btn-secondary"
          style={{ padding: "8px 16px", borderRadius: "6px", border: "1px solid var(--border)", background: "var(--surface)", opacity: offset === 0 ? 0.5 : 1, cursor: offset === 0 ? "default" : "pointer" }}
        >
          Previous
        </button>
        <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
          Page {Math.floor(offset / limit) + 1}
        </span>
        <button 
          disabled={files.length < limit} 
          onClick={() => setOffset(offset + limit)}
          className="btn btn-secondary"
          style={{ padding: "8px 16px", borderRadius: "6px", border: "1px solid var(--border)", background: "var(--surface)", opacity: files.length < limit ? 0.5 : 1, cursor: files.length < limit ? "default" : "pointer" }}
        >
          Next
        </button>
      </div>
    </section>
  );
}
