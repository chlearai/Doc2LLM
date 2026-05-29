"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { LogIn, UserPlus } from "lucide-react";
import { FormEvent, Suspense, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DEV_AUTH_COOKIE, DEV_AUTH_EMAIL, DEV_AUTH_PASSWORD, hasSupabaseEnvironment } from "@/lib/env";
import { createSupabaseBrowserClient } from "@/lib/supabase-browser";
import { signUp } from "@/lib/api-client";

function LoginForm({
  isSignUp,
  setIsSignUp,
}: {
  isSignUp: boolean;
  setIsSignUp: (val: boolean) => void;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const submittedEmail = String(formData.get("email") ?? "").trim();
    const submittedPassword = String(formData.get("password") ?? "");
    const submittedFullName = String(formData.get("fullName") ?? "").trim();
    const submittedConfirmPassword = String(formData.get("confirmPassword") ?? "");
    
    setLoading(true);
    setError("");
    setSuccess("");

    // Email validation regex check
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(submittedEmail)) {
      setLoading(false);
      setError("Please enter a valid email address.");
      return;
    }

    // Password validations (letters and numbers)
    if (isSignUp) {
      if (!submittedFullName) {
        setLoading(false);
        setError("Please enter your full name.");
        return;
      }
      if (submittedPassword.length < 8) {
        setLoading(false);
        setError("Password must be at least 8 characters long.");
        return;
      }
      if (!/[a-zA-Z]/.test(submittedPassword) || !/[0-9]/.test(submittedPassword)) {
        setLoading(false);
        setError("Password must contain both letters and numbers.");
        return;
      }
      if (submittedPassword !== submittedConfirmPassword) {
        setLoading(false);
        setError("Passwords do not match.");
        return;
      }
    }

    if (!hasSupabaseEnvironment()) {
      setLoading(false);
      if (isSignUp) {
        setError("Sign up is only supported when Supabase Auth is enabled. Use the local credentials to sign in.");
        return;
      }
      if (submittedEmail === DEV_AUTH_EMAIL && submittedPassword === DEV_AUTH_PASSWORD) {
        document.cookie = `${DEV_AUTH_COOKIE}=user; path=/; max-age=86400; SameSite=Lax`;
        router.replace(searchParams.get("next") || "/dashboard");
        router.refresh();
        return;
      }
      if (submittedEmail === "admin@local.test" && submittedPassword === "markdown-admin") {
        document.cookie = `${DEV_AUTH_COOKIE}=admin; path=/; max-age=86400; SameSite=Lax`;
        router.replace(searchParams.get("next") || "/admin");
        router.refresh();
        return;
      }
      setError("Use the local dev credentials shown below, or configure Supabase Auth.");
      return;
    }

    if (isSignUp) {
      try {
        await signUp(submittedEmail, submittedPassword, submittedFullName);
        setSuccess("Account created! Check your email for a confirmation link.");
        setFullName("");
        setEmail("");
        setPassword("");
        setConfirmPassword("");
      } catch (err: any) {
        setError(err.message || "Registration failed. Try again.");
      } finally {
        setLoading(false);
      }
    } else {
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
  }

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      {isSignUp && (
        <Input
          label="Full Name"
          name="fullName"
          type="text"
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          required
        />
      )}
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
        autoComplete={isSignUp ? "new-password" : "current-password"}
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        required
      />
      {isSignUp && (
        <Input
          label="Confirm Password"
          name="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          error={error}
          required
        />
      )}
      
      {!isSignUp && error ? <p className="message error-message">{error}</p> : null}
      {success ? <p className="message success-message">{success}</p> : null}

      <Button 
        type="submit" 
        loading={loading} 
        icon={isSignUp ? <UserPlus size={16} aria-hidden="true" /> : <LogIn size={16} aria-hidden="true" />}
      >
        {isSignUp ? "Sign up" : "Sign in"}
      </Button>


      <div style={{ display: "flex", justifyContent: "center", marginTop: "8px" }}>
        <button
          type="button"
          onClick={() => {
            setIsSignUp(!isSignUp);
            setError("");
            setSuccess("");
          }}
          className="text-link"
          style={{ background: "none", border: "none", cursor: "pointer", padding: "4px" }}
        >
          {isSignUp ? "Already have an account? Sign in" : "Don't have an account? Sign up"}
        </button>
      </div>

      {!hasSupabaseEnvironment() && !isSignUp ? (
        <p className="dev-auth-note" style={{ marginTop: "12px", fontSize: "0.85rem", color: "var(--foreground-muted)", textAlign: "center", lineHeight: "1.5" }}>
          Local dev logins:<br/>
          User: <strong>{DEV_AUTH_EMAIL}</strong> / <strong>{DEV_AUTH_PASSWORD}</strong><br/>
          Admin: <strong>admin@local.test</strong> / <strong>markdown-admin</strong>
        </p>
      ) : null}
    </form>
  );
}

export default function LoginPage() {
  const [isSignUp, setIsSignUp] = useState(false);

  return (
    <main className="login-page">
      <section className="login-panel" aria-labelledby="login-title">
        <div style={{ textAlign: "center", marginBottom: "20px" }}>
          <img src="/favicon.svg" alt="" width="80" height="45" style={{ objectFit: "contain", display: "block", margin: "0 auto 12px" }} />
          <p className="eyebrow" style={{ margin: 0 }}>Doc2LLM</p>
        </div>
        <div>
          <h1 id="login-title" style={{ textAlign: "center" }}>
            {isSignUp ? "Create your account" : "Sign in to Doc2LLM"}
          </h1>
          <p className="login-copy" style={{ textAlign: "center" }}>
            {isSignUp 
              ? "Register to start converting documents into clean, LLM-friendly Markdown."
              : "Convert documents into clean, LLM-friendly Markdown through a secure, focused workspace."
            }
          </p>
        </div>
        <Suspense>
          <LoginForm isSignUp={isSignUp} setIsSignUp={setIsSignUp} />
        </Suspense>
      </section>
    </main>
  );
}
