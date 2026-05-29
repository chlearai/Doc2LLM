export function getSupabaseUrl() {
  return process.env.NEXT_PUBLIC_SUPABASE_URL || "http://localhost:54321";
}

export function getSupabaseAnonKey() {
  return process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "local-anon-key";
}

export function getApiBaseUrl() {
  const value = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const trimmed = value.trim().replace(/\/+$/, "");
  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }
  if (
    trimmed.startsWith("localhost") ||
    trimmed.startsWith("127.") ||
    trimmed.startsWith("[::1]")
  ) {
    return `http://${trimmed}`;
  }
  return `https://${trimmed}`;
}

export function hasSupabaseEnvironment() {
  return Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
}

export const DEV_AUTH_EMAIL = "dev@local.test";
export const DEV_AUTH_PASSWORD = "markdown-dev";
export const DEV_AUTH_COOKIE = "markit_dev_auth";
export const DEV_ADMIN_EMAIL = "admin@local.test";
export const DEV_ADMIN_PASSWORD = "markdown-admin";
