"use client";

import { useEffect, useState } from "react";
import { UserPlus, Search, UserCheck, UserX, Shield, User } from "lucide-react";
import { createApiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type UserProfile = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  files_converted: number;
  ocr_tokens_consumed: number;
};

export default function AdminUsers() {
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  
  // Pagination
  const [offset, setOffset] = useState(0);
  const limit = 10;
  
  // Add User Form State
  const [showAddForm, setShowAddForm] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newName, setNewName] = useState("");
  const [newRole, setNewRole] = useState("user");
  const [adding, setAdding] = useState(false);

  async function loadUsers(currentSearch = search, currentOffset = offset) {
    setLoading(true);
    setError("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      const data = await client.listAdminUsers(currentSearch, limit, currentOffset);
      setUsers(data.items);
    } catch (err: any) {
      setError(err?.message || "Failed to load users list.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers(search, offset);
  }, [offset]);

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setOffset(0);
    loadUsers(search, 0);
  }

  async function handleAddUser(e: React.FormEvent) {
    e.preventDefault();
    if (!newEmail) return;
    setAdding(true);
    setError("");
    setNotice("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      await client.createAdminUser(newEmail, newName || undefined, newRole);
      setNotice(`User ${newEmail} created successfully.`);
      setNewEmail("");
      setNewName("");
      setNewRole("user");
      setShowAddForm(false);
      loadUsers(search, offset);
    } catch (err: any) {
      setError(err?.message || "Failed to add user.");
    } finally {
      setAdding(false);
    }
  }

  async function toggleStatus(user: UserProfile) {
    setError("");
    setNotice("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      const nextActive = !user.is_active;
      await client.updateAdminUserStatus(user.id, nextActive);
      setNotice(`User ${user.email} is now ${nextActive ? "enabled" : "disabled"}.`);
      loadUsers(search, offset);
    } catch (err: any) {
      setError(err?.message || "Failed to update user status.");
    }
  }

  async function toggleRole(user: UserProfile) {
    setError("");
    setNotice("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Please sign in again.");
      const client = createApiClient(token);
      const nextRole = user.role === "admin" ? "user" : "admin";
      await client.updateAdminUserRole(user.id, nextRole);
      setNotice(`User ${user.email} role updated to ${nextRole}.`);
      loadUsers(search, offset);
    } catch (err: any) {
      setError(err?.message || "Failed to update user role.");
    }
  }

  return (
    <section className="page-panel" style={{ animation: "fadeInSlideUp 0.3s var(--ease-out-quart) forwards" }}>
      <div className="section-heading" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <p className="eyebrow">Admin Portal</p>
          <h1>Users</h1>
        </div>
        <Button 
          type="button" 
          onClick={() => setShowAddForm(!showAddForm)}
          icon={<UserPlus size={16} />}
        >
          {showAddForm ? "Cancel Adding" : "Add User"}
        </Button>
      </div>

      {showAddForm && (
        <form 
          onSubmit={handleAddUser} 
          style={{ 
            background: "var(--surface)", 
            border: "1px solid var(--border)", 
            padding: "20px", 
            borderRadius: "8px", 
            margin: "16px 0", 
            display: "grid", 
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", 
            gap: "16px",
            alignItems: "end"
          }}
        >
          <Input 
            label="Email Address" 
            type="email" 
            value={newEmail} 
            onChange={(e) => setNewEmail(e.target.value)} 
            required 
          />
          <Input 
            label="Full Name" 
            type="text" 
            value={newName} 
            onChange={(e) => setNewName(e.target.value)} 
          />
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--text-muted)" }}>Role</label>
            <select 
              value={newRole} 
              onChange={(e) => setNewRole(e.target.value)}
              style={{
                height: "40px",
                padding: "0 12px",
                borderRadius: "6px",
                border: "1px solid var(--border)",
                background: "var(--background)",
                color: "var(--text)",
              }}
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <Button type="submit" loading={adding}>Save User</Button>
        </form>
      )}

      <form onSubmit={handleSearchSubmit} style={{ display: "flex", gap: "8px", margin: "20px 0" }}>
        <div style={{ flex: 1, position: "relative" }}>
          <Search size={16} style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
          <input 
            type="text" 
            placeholder="Search users by name or email..." 
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

      {error ? <p className="message error-message">{error}</p> : null}
      {notice ? <p className="message success-message">{notice}</p> : null}

      {loading ? (
        <div className="skeleton-list" style={{ height: "300px" }} />
      ) : (
        <div className="table-responsive" style={{ overflowX: "auto", margin: "16px 0" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)", paddingBottom: "10px" }}>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>User</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Role</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Status</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Conversions</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>OCR Tokens</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Joined Date</th>
                <th style={{ padding: "12px", fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} style={{ borderBottom: "1px solid var(--border)", height: "60px" }}>
                  <td style={{ padding: "12px" }}>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontWeight: 600 }}>{user.full_name || "No name"}</span>
                      <span style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>{user.email}</span>
                    </div>
                  </td>
                  <td style={{ padding: "12px" }}>
                    <span 
                      style={{ 
                        display: "inline-flex", 
                        alignItems: "center", 
                        gap: "4px",
                        fontSize: "var(--text-xs)",
                        fontWeight: 600,
                        padding: "4px 8px",
                        borderRadius: "12px",
                        background: user.role === "admin" ? "var(--surface-muted)" : "var(--background)",
                        border: "1px solid var(--border)"
                      }}
                    >
                      {user.role === "admin" ? <Shield size={12} style={{ color: "var(--primary)" }} /> : <User size={12} />}
                      {user.role}
                    </span>
                  </td>
                  <td style={{ padding: "12px" }}>
                    <span 
                      style={{
                        display: "inline-block",
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        background: user.is_active ? "var(--success)" : "var(--error)",
                        marginRight: "6px"
                      }}
                    />
                    <span style={{ fontSize: "var(--text-sm)", fontWeight: 500 }}>
                      {user.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td style={{ padding: "12px", fontSize: "var(--text-sm)", fontWeight: 600 }}>{user.files_converted}</td>
                  <td style={{ padding: "12px", fontSize: "var(--text-sm)", fontWeight: 600 }}>{user.ocr_tokens_consumed.toLocaleString()}</td>
                  <td style={{ padding: "12px", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: "12px", textAlign: "right" }}>
                    <div style={{ display: "inline-flex", gap: "8px" }}>
                      <Button 
                        type="button" 
                        variant="secondary"
                        onClick={() => toggleRole(user)}
                        style={{ padding: "4px 10px", fontSize: "0.8rem", height: "32px" }}
                      >
                        Change Role
                      </Button>
                      <Button 
                        type="button" 
                        variant="secondary"
                        onClick={() => toggleStatus(user)}
                        style={{ padding: "4px 10px", fontSize: "0.8rem", height: "32px", color: user.is_active ? "var(--error)" : "var(--success)" }}
                        icon={user.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                      >
                        {user.is_active ? "Disable" : "Enable"}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
                    No users found matching the query.
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
          disabled={users.length < limit} 
          onClick={() => setOffset(offset + limit)}
          style={{ minHeight: "36px", padding: "0 16px" }}
        >
          Next
        </Button>
      </div>
    </section>
  );
}
