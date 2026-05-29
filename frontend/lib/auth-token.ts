"use client";

import { hasSupabaseEnvironment } from "./env";
import { createSupabaseBrowserClient } from "./supabase-browser";

export async function getAccessToken() {
  if (!hasSupabaseEnvironment()) {
    const isDevAdmin = typeof document !== "undefined" && 
      document.cookie.split(";").some((c) => c.trim() === "doc2llm_dev_auth=admin");
    return isDevAdmin ? "local-admin-token" : "local-dev-token";
  }

  const supabase = createSupabaseBrowserClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? "";
}
