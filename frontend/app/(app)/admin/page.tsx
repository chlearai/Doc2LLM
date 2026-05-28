"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, Users, FileText, AlertTriangle, Play, CheckCircle, RefreshCw } from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";

type Stats = {
  total_users: number;
  total_converted_files: number;
  files_processed_today: number;
  failed_conversions: number;
  pending_conversions: number;
  system_health: string;
};

type Health = {
  railway_converter: { status: string; message?: string };
  supabase_connection: { status: string; message?: string };
  conversion_queue: { status: string; message?: string };
  storage_write: { status: string; message?: string };
};

export default function AdminOverview() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      const [statsData, healthData] = await Promise.all([
        client.getAdminStats(),
        client.getAdminSystemHealth(),
      ]);
      setStats(statsData);
      setHealth(healthData);
    } catch (err: any) {
      setError(err?.message || "Failed to load admin overview data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="page-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Admin Portal</p>
            <h1>Overview</h1>
          </div>
        </div>
        <div className="skeleton-list" style={{ height: "200px" }} />
      </div>
    );
  }

  return (
    <section className="page-panel" style={{ animation: "fadeInSlideUp 0.3s var(--ease-out-quart) forwards" }}>
      <div className="section-heading" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <p className="eyebrow">Admin Portal</p>
          <h1>Overview</h1>
        </div>
        <button 
          onClick={loadData}
          className="btn btn-secondary"
          style={{ padding: "8px 16px", borderRadius: "6px", background: "var(--surface)", border: "1px solid var(--border)", cursor: "pointer" }}
        >
          Refresh Data
        </button>
      </div>

      {error ? <p className="message error-message">{error}</p> : null}

      {stats && (
        <div 
          className="admin-stats-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "20px",
            margin: "24px 0"
          }}
        >
          <div className="card" style={{ padding: "20px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>Total Users</span>
              <Users size={20} style={{ color: "var(--primary)" }} />
            </div>
            <p style={{ fontSize: "2rem", margin: 0, fontWeight: 700, color: "var(--text)" }}>{stats.total_users}</p>
          </div>

          <div className="card" style={{ padding: "20px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>Files Converted</span>
              <FileText size={20} style={{ color: "var(--primary)" }} />
            </div>
            <p style={{ fontSize: "2rem", margin: 0, fontWeight: 700, color: "var(--text)" }}>{stats.total_converted_files}</p>
          </div>

          <div className="card" style={{ padding: "20px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>Conversions Today</span>
              <Play size={20} style={{ color: "var(--success)" }} />
            </div>
            <p style={{ fontSize: "2rem", margin: 0, fontWeight: 700, color: "var(--text)" }}>{stats.files_processed_today}</p>
          </div>

          <div className="card" style={{ padding: "20px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>Failed Jobs</span>
              <AlertTriangle size={20} style={{ color: "var(--error)" }} />
            </div>
            <p style={{ fontSize: "2rem", margin: 0, fontWeight: 700, color: "var(--text)" }}>{stats.failed_conversions}</p>
          </div>

          <div className="card" style={{ padding: "20px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>Queue Backlog</span>
              <RefreshCw size={20} style={{ color: "var(--warning)" }} />
            </div>
            <p style={{ fontSize: "2rem", margin: 0, fontWeight: 700, color: "var(--text)" }}>{stats.pending_conversions}</p>
          </div>
        </div>
      )}

      {health && (
        <div style={{ marginTop: "32px" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 650, marginBottom: "16px", letterSpacing: "-0.015em" }}>System Infrastructure Health</h2>
          
          <div 
            className="system-health-grid"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "16px"
            }}
          >
            {[
              { title: "Railway Converter Service", indicator: health.railway_converter },
              { title: "Supabase Connection Status", indicator: health.supabase_connection },
              { title: "In-App Conversion Queue", indicator: health.conversion_queue },
              { title: "Supabase Storage Bucket Status", indicator: health.storage_write },
            ].map((srv, idx) => {
              const statusColor = srv.indicator.status === "Healthy" 
                ? "var(--success)" 
                : srv.indicator.status === "Warning" 
                ? "var(--warning)" 
                : "var(--error)";
              
              return (
                <div 
                  key={idx}
                  style={{
                    padding: "16px",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    background: "var(--surface)",
                    display: "flex",
                    alignItems: "center",
                    gap: "12px"
                  }}
                >
                  {srv.indicator.status === "Healthy" ? (
                    <CheckCircle size={24} style={{ color: "var(--success)" }} />
                  ) : (
                    <AlertTriangle size={24} style={{ color: "var(--warning)" }} />
                  )}
                  <div>
                    <h3 style={{ fontSize: "0.95rem", margin: 0, fontWeight: 600 }}>{srv.title}</h3>
                    <p style={{ fontSize: "0.85rem", color: statusColor, margin: "2px 0 0", fontWeight: 500 }}>
                      {srv.indicator.status}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
