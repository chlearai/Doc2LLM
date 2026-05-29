"use client";

import { useEffect, useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { User, Lock, Trash2, ShieldAlert, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiClientError, createApiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { DEV_AUTH_COOKIE, hasSupabaseEnvironment } from "@/lib/env";
import { createSupabaseBrowserClient } from "@/lib/supabase-browser";

export default function SettingsPage() {
  const router = useRouter();
  
  // Profile state
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [originalName, setOriginalName] = useState("");
  const [role, setRole] = useState("user");
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileSuccess, setProfileSuccess] = useState("");
  const [profileError, setProfileError] = useState("");
  const [profileSaving, setProfileSaving] = useState(false);

  // Password change state
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);

  // Delete account state
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  useEffect(() => {
    async function loadProfile() {
      try {
        const token = await getAccessToken();
        if (!token) {
          router.replace("/login");
          return;
        }
        const client = createApiClient(token);
        const profile = await client.me();
        setEmail(profile.email);
        setFullName(profile.full_name || "");
        setOriginalName(profile.full_name || "");
        setRole(profile.role);
      } catch (err: any) {
        console.error("Failed to load settings profile:", err);
        setProfileError(err.message || "Failed to load account information.");
      } finally {
        setProfileLoading(false);
      }
    }

    loadProfile();
  }, [router]);

  async function handleUpdateProfile(e: FormEvent) {
    e.preventDefault();
    if (!fullName.trim()) {
      setProfileError("Please enter your full name.");
      return;
    }

    setProfileSaving(true);
    setProfileError("");
    setProfileSuccess("");

    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Authentication token missing. Please sign in again.");
      const client = createApiClient(token);
      const updated = await client.updateProfile(fullName.trim());
      setFullName(updated.full_name || "");
      setOriginalName(updated.full_name || "");
      setProfileSuccess("Profile updated successfully.");
    } catch (err: any) {
      setProfileError(err.message || "Failed to update profile.");
    } finally {
      setProfileSaving(false);
    }
  }

  async function handleChangePassword(e: FormEvent) {
    e.preventDefault();
    
    // Validations
    if (newPassword.length < 8) {
      setPasswordError("Password must be at least 8 characters long.");
      return;
    }
    if (!/[a-zA-Z]/.test(newPassword) || !/[0-9]/.test(newPassword)) {
      setPasswordError("Password must contain both letters and numbers.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("Passwords do not match.");
      return;
    }

    setPasswordSaving(true);
    setPasswordError("");
    setPasswordSuccess("");

    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Authentication token missing. Please sign in again.");
      const client = createApiClient(token);
      await client.changePassword(newPassword);
      setPasswordSuccess("Password updated successfully.");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setPasswordError(err.message || "Failed to change password.");
    } finally {
      setPasswordSaving(false);
    }
  }

  async function handleDeleteAccount() {
    setDeleteLoading(true);
    setDeleteError("");

    try {
      const token = await getAccessToken();
      if (token) {
        const client = createApiClient(token);
        await client.deleteAccount();
      }

      if (!hasSupabaseEnvironment()) {
        document.cookie = `${DEV_AUTH_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
      } else {
        const supabase = createSupabaseBrowserClient();
        await supabase.auth.signOut();
      }

      router.replace("/login");
      router.refresh();
    } catch (err: any) {
      setDeleteError(err.message || "Failed to delete account. Please try again.");
      setDeleteLoading(false);
    }
  }

  if (profileLoading) {
    return (
      <section className="page-panel">
        <div style={{ padding: "40px 0", textAlign: "center", color: "var(--text-muted)" }}>
          Loading account settings...
        </div>
      </section>
    );
  }

  return (
    <section className="page-panel" style={{ maxWidth: "800px", margin: "0 auto" }}>
      <div className="section-heading" style={{ marginBottom: "32px" }}>
        <div>
          <p className="eyebrow">Account</p>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 750 }}>Settings</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginTop: "4px" }}>
            Manage your profile details, change security settings, or close your account.
          </p>
        </div>
      </div>

      {/* Profile details form */}
      <form onSubmit={handleUpdateProfile} style={{ display: "grid", gap: "20px" }}>
        <h2 style={{ fontSize: "1.125rem", fontWeight: 650, display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
          <User size={18} style={{ color: "var(--primary)" }} />
          <span>Profile Details</span>
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <Input
            label="Email Address"
            type="email"
            value={email}
            disabled
            hint="Email cannot be changed."
          />
          <Input
            label="Full Name"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Your full name"
            required
          />
        </div>

        {profileError && <p className="message error-message" style={{ margin: 0 }}>{profileError}</p>}
        {profileSuccess && <p className="message success-message" style={{ margin: 0 }}>{profileSuccess}</p>}

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <Button
            type="submit"
            loading={profileSaving}
            disabled={fullName.trim() === originalName.trim() || !fullName.trim()}
          >
            Save Changes
          </Button>
        </div>
      </form>

      <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "32px 0" }} />

      {/* Password reset form */}
      <form onSubmit={handleChangePassword} style={{ display: "grid", gap: "20px" }}>
        <h2 style={{ fontSize: "1.125rem", fontWeight: 650, display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
          <Lock size={18} style={{ color: "var(--primary)" }} />
          <span>Change Password</span>
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <Input
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="At least 8 characters"
            required
            hint="Must contain both letters and numbers."
          />
          <Input
            label="Confirm New Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Repeat new password"
            required
          />
        </div>

        {passwordError && <p className="message error-message" style={{ margin: 0 }}>{passwordError}</p>}
        {passwordSuccess && <p className="message success-message" style={{ margin: 0 }}>{passwordSuccess}</p>}

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <Button
            type="submit"
            loading={passwordSaving}
            disabled={!newPassword || !confirmPassword}
          >
            Update Password
          </Button>
        </div>
      </form>

      <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "32px 0" }} />

      {/* Danger Zone */}
      <div style={{ display: "grid", gap: "16px" }}>
        <h2 style={{ fontSize: "1.125rem", fontWeight: 650, display: "flex", alignItems: "center", gap: "8px", margin: 0, color: "var(--error)" }}>
          <Trash2 size={18} />
          <span>Danger Zone</span>
        </h2>

        <div 
          style={{ 
            border: "1px solid var(--border)", 
            borderRadius: "8px", 
            padding: "20px", 
            backgroundColor: "color-mix(in oklch, var(--error) 4%, var(--surface))",
            display: "grid",
            gap: "16px"
          }}
        >
          <div>
            <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 6px" }}>Delete Account</h3>
            <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", margin: 0, lineHeight: 1.5 }}>
              Permanently delete your profile, conversion logs, and all your converted Markdown output files. 
              This action cannot be undone and you will lose access immediately.
            </p>
          </div>

          {deleteError && <p className="message error-message" style={{ margin: 0 }}>{deleteError}</p>}

          {!deleteConfirm ? (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <button
                type="button"
                className="button button-ghost"
                style={{ 
                  color: "var(--error)", 
                  borderColor: "color-mix(in oklch, var(--error) 30%, var(--border))",
                  backgroundColor: "var(--surface)" 
                }}
                onClick={() => setDeleteConfirm(true)}
              >
                Delete Account
              </button>
            </div>
          ) : (
            <div 
              style={{ 
                border: "1px solid color-mix(in oklch, var(--error) 20%, var(--border))", 
                borderRadius: "6px", 
                padding: "16px", 
                backgroundColor: "var(--surface)",
                display: "grid",
                gap: "12px"
              }}
            >
              <p style={{ margin: 0, fontSize: "0.875rem", fontWeight: 550, color: "var(--text)" }}>
                Are you absolutely sure you want to delete your account? This is a permanent action.
              </p>
              <div style={{ display: "flex", gap: "10px" }}>
                <Button
                  type="button"
                  variant="primary"
                  loading={deleteLoading}
                  style={{ backgroundColor: "var(--error)", color: "white" }}
                  onClick={handleDeleteAccount}
                >
                  Yes, delete my account
                </Button>
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => setDeleteConfirm(false)}
                  disabled={deleteLoading}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
