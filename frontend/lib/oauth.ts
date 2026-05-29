"use client";

function normalizeOrigin(origin: string) {
  const trimmed = origin.trim().replace(/\/+$/, "");
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

export function getAppOrigin() {
  if (typeof window !== "undefined" && window.location.origin) {
    return window.location.origin;
  }
  return normalizeOrigin(process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000");
}

export function buildOAuthRedirectTo(nextPath = "/dashboard", origin = getAppOrigin()) {
  const safeNextPath = nextPath.startsWith("/") ? nextPath : "/dashboard";
  const url = new URL("/auth/callback", normalizeOrigin(origin));
  url.searchParams.set("next", safeNextPath);
  return url.toString();
}
