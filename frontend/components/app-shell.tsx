"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FileText, History, LogOut, Settings } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "./ui/button";
import { DEV_AUTH_COOKIE, DEV_AUTH_EMAIL, hasSupabaseEnvironment } from "@/lib/env";
import { createSupabaseBrowserClient } from "@/lib/supabase-browser";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: FileText },
  { href: "/history", label: "History", icon: History },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState<string>("Loading account");

  useEffect(() => {
    if (!hasSupabaseEnvironment()) {
      setEmail(DEV_AUTH_EMAIL);
      return;
    }
    const supabase = createSupabaseBrowserClient();
    supabase.auth.getUser().then(({ data }) => {
      setEmail(data.user?.email ?? "Signed in");
    });
  }, []);

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

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link href="/dashboard" className="brand" aria-label="Doc2LLM home">
          <img src="/favicon.svg" alt="" width="32" height="18" style={{ objectFit: "contain" }} />
          <span>Doc2LLM</span>
        </Link>
        <nav className="nav" aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname.startsWith(item.href);
            return (
              <Link key={item.href} href={item.href} className={active ? "nav-link active" : "nav-link"}>
                <Icon size={16} aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="account">
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
