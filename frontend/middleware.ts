import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import type { CookieOptions } from "@supabase/ssr";
import { DEV_AUTH_COOKIE, getSupabaseAnonKey, getSupabaseUrl, hasSupabaseEnvironment } from "./lib/env";

const protectedRoutes = ["/dashboard", "/history", "/settings", "/conversions", "/admin"];

export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const isProtected = protectedRoutes.some((route) => pathname.startsWith(route));
  const isLocalHost = ["localhost", "127.0.0.1", "::1"].includes(request.nextUrl.hostname);

  if (!hasSupabaseEnvironment()) {
    const devAuthVal = request.cookies.get(DEV_AUTH_COOKIE)?.value;
    const hasDevAuth = isLocalHost && (devAuthVal === "user" || devAuthVal === "admin");
    const isDevAdmin = isLocalHost && devAuthVal === "admin";

    if (isProtected) {
      if (pathname.startsWith("/admin") && !isDevAdmin) {
        const dashboardUrl = request.nextUrl.clone();
        dashboardUrl.pathname = "/dashboard";
        return NextResponse.redirect(dashboardUrl);
      }
      if (hasDevAuth) {
        return NextResponse.next();
      }
      const loginUrl = request.nextUrl.clone();
      loginUrl.pathname = "/login";
      loginUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(loginUrl);
    }
    if (pathname === "/login" && hasDevAuth) {
      const targetUrl = request.nextUrl.clone();
      targetUrl.pathname = isDevAdmin ? "/admin" : "/dashboard";
      targetUrl.search = "";
      return NextResponse.redirect(targetUrl);
    }
    return NextResponse.next();
  }

  let response = NextResponse.next({ request });
  const supabase = createServerClient(getSupabaseUrl(), getSupabaseAnonKey(), {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet: { name: string; value: string; options: CookieOptions }[]) {
        cookiesToSet.forEach(({ name, value, options }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
      },
    },
  });

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (isProtected && !user) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (pathname === "/login" && user) {
    const dashboardUrl = request.nextUrl.clone();
    dashboardUrl.pathname = "/dashboard";
    dashboardUrl.search = "";
    return NextResponse.redirect(dashboardUrl);
  }

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
