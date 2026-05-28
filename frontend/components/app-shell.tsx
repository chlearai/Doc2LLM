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
  const [email, setEmail] = useState<string>("Loading account");
  const [role, setRole] = useState<string>("user");

  useEffect(() => {
    async function loadProfile() {
      try {
        const token = await getAccessToken();
        if (!token) {
          setEmail("Not signed in");
          return;
        }
        const client = createApiClient(token);
        const profile = await client.me();
        setEmail(profile.email);
        setRole(profile.role);
        
        // Client-side role protection: if on /admin but not admin, redirect to /dashboard
        if (pathname.startsWith("/admin") && profile.role !== "admin") {
          router.replace("/dashboard");
        }
      } catch (err) {
        console.error("Failed to load user profile", err);
        if (!hasSupabaseEnvironment()) {
          setEmail(DEV_AUTH_EMAIL);
        } else {
          setEmail("Signed in");
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
        <Link href={role === "admin" ? "/admin" : "/dashboard"} className="brand" aria-label="Doc2LLM home">
          <img src="/favicon.svg" alt="" width="32" height="18" style={{ objectFit: "contain" }} />
          <span>Doc2LLM</span>
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
            <Link 
              href={pathname.startsWith("/admin") ? "/dashboard" : "/admin"}
              className="nav-link"
              style={{ marginRight: "16px", color: "var(--color-primary-600)", fontWeight: 500, display: "inline-flex", alignItems: "center", gap: "6px" }}
            >
              <ShieldAlert size={16} />
              <span>{pathname.startsWith("/admin") ? "App Mode" : "Admin Mode"}</span>
            </Link>
          )}
          <span title={email}>{email}</span>
          <Button variant="ghost" type="button" onClick={signOut} icon={<LogOut size={16} aria-hidden="true" />}>
            Sign out
          </Button>
        </div>
      </header>
      <main className="shell-main">{children}</main>
    </div>
  );
}
