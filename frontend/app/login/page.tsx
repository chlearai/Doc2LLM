"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { LogIn } from "lucide-react";
import { FormEvent, Suspense, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DEV_AUTH_COOKIE, DEV_AUTH_EMAIL, DEV_AUTH_PASSWORD, hasSupabaseEnvironment } from "@/lib/env";
import { createSupabaseBrowserClient } from "@/lib/supabase-browser";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const submittedEmail = String(formData.get("email") ?? "");
    const submittedPassword = String(formData.get("password") ?? "");
    setLoading(true);
    setError("");

    if (!hasSupabaseEnvironment()) {
      setLoading(false);
      if (submittedEmail === DEV_AUTH_EMAIL && submittedPassword === DEV_AUTH_PASSWORD) {
        document.cookie = `${DEV_AUTH_COOKIE}=1; path=/; max-age=86400; SameSite=Lax`;
        router.replace(searchParams.get("next") || "/dashboard");
        router.refresh();
        return;
      }
      setError("Use the local dev credentials shown below, or configure Supabase Auth.");
      return;
    }

    const supabase = createSupabaseBrowserClient();
    const { error: signInError } = await supabase.auth.signInWithPassword({
      email: submittedEmail,
      password: submittedPassword,
    });
    setLoading(false);

    if (signInError) {
      setError("Sign in failed. Check your email and password, then try again.");
      return;
    }

    router.replace(searchParams.get("next") || "/dashboard");
    router.refresh();
  }

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <Input
        label="Email"
        name="email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        required
      />
      <Input
        label="Password"
        name="password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        error={error}
        required
      />
      <Button type="submit" loading={loading} icon={<LogIn size={16} aria-hidden="true" />}>
        Sign in
      </Button>
      {!hasSupabaseEnvironment() ? (
        <p className="dev-auth-note">
          Local dev login: <strong>{DEV_AUTH_EMAIL}</strong> / <strong>{DEV_AUTH_PASSWORD}</strong>
        </p>
      ) : null}
    </form>
  );
}

export default function LoginPage() {
  return (
    <main className="login-page">
      <section className="login-panel" aria-labelledby="login-title">
        <div>
          <p className="eyebrow">Internal dashboard</p>
          <h1 id="login-title">Sign in to Markdown Dashboard</h1>
          <p className="login-copy">Convert documents into clean Markdown through a focused, secure workspace.</p>
        </div>
        <Suspense>
          <LoginForm />
        </Suspense>
      </section>
    </main>
  );
}
