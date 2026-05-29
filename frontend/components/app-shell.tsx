"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FileText, History, LogOut, Settings, LayoutDashboard, Users, RefreshCw, Terminal, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "./ui/button";
import { DEV_AUTH_COOKIE, DEV_AUTH_EMAIL, hasSupabaseEnvironment } from "@/lib/env";
import { createSupabaseBrowserClient } from "@/lib/supabase-browser";
import { createApiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: FileText, exact: false },
  { href: "/history", label: "History", icon: History, exact: false },
  { href: "/settings", label: "Settings", icon: Settings, exact: false },
];

const adminNavItems = [
  { href: "/admin", label: "Overview", icon: LayoutDashboard, exact: true },
  { href: "/admin/users", label: "Users", icon: Users, exact: false },
  { href: "/admin/files", label: "Files", icon: FileText, exact: false },
  { href: "/admin/conversions", label: "Conversions", icon: RefreshCw, exact: false },
  { href: "/admin/logs", label: "Logs", icon: Terminal, exact: false },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [accountLabel, setAccountLabel] = useState<string>("Loading account");
  const [accountTitle, setAccountTitle] = useState<string>("Loading account");
  const [role, setRole] = useState<string>("user");

  useEffect(() => {
    async function loadProfile() {
      try {
        const token = await getAccessToken();
        if (!token) {
          setAccountLabel("Not signed in");
          setAccountTitle("Not signed in");
          return;
        }
        const client = createApiClient(token);
        const profile = await client.me();
        const name = profile.full_name?.trim() || profile.email;
        setAccountLabel(`Hello, ${name}`);
        setAccountTitle(profile.email);
        setRole(profile.role);
        
        // Client-side role protection: if on /admin but not admin, redirect to /dashboard
        if (pathname.startsWith("/admin") && profile.role !== "admin") {
          router.replace("/dashboard");
        }
      } catch (err) {
        console.error("Failed to load user profile", err);
        if (!hasSupabaseEnvironment()) {
          setAccountLabel(`Hello, ${DEV_AUTH_EMAIL}`);
          setAccountTitle(DEV_AUTH_EMAIL);
        } else {
          setAccountLabel("Hello, signed in");
          setAccountTitle("Signed in");
        }
      }
    }
    loadProfile();
  }, [pathname]);

  async function signOut() {
    if (!hasSupabaseEnvironment()) {
      document.cookie = `${DEV_AUTH_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
      router.replace("/login");
      router.refresh();
      return;
    }
    const supabase = createSupabaseBrowserClient();
    await supabase.auth.signOut();
    router.replace("/login");
    router.refresh();
  }

  const activeNavItems = pathname.startsWith("/admin") ? adminNavItems : navItems;

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link href={role === "admin" ? "/admin" : "/dashboard"} className="brand" aria-label="MarkIt home">
          <img src="/favicon.png" alt="" width="32" height="18" style={{ objectFit: "contain" }} />
          <span>MarkIt</span>
        </Link>
        <nav className="nav" aria-label="Primary navigation">
          {activeNavItems.map((item) => {
            const Icon = item.icon;
            const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
            return (
              <Link key={item.href} href={item.href} className={active ? "nav-link active" : "nav-link"}>
                <Icon size={16} aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="account">
          {role === "admin" && (
            <div className="mode-toggle-container">
              <span className={`mode-label ${!pathname.startsWith("/admin") ? "active" : ""}`}>App Mode</span>
              <div className="toggle-border">
                <input 
                  id="admin-mode-toggle" 
                  type="checkbox" 
                  checked={pathname.startsWith("/admin")}
                  onChange={(e) => {
                    if (e.target.checked) {
                      router.push("/admin");
                    } else {
                      router.push("/dashboard");
                    }
                  }}
                />
                <label htmlFor="admin-mode-toggle">
                  <div className="handle"></div>
                </label>
              </div>
              <span className={`mode-label ${pathname.startsWith("/admin") ? "active" : ""}`}>Admin Mode</span>
            </div>
          )}
          <span title={accountTitle}>{accountLabel}</span>
          <Button variant="ghost" type="button" onClick={signOut} icon={<LogOut size={16} aria-hidden="true" />}>
            Sign out
          </Button>
        </div>
      </header>
      <main className="shell-main">{children}</main>
    </div>
  );
}
