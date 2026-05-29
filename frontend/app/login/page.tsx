"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { LogIn, UserPlus } from "lucide-react";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DEV_AUTH_COOKIE, DEV_AUTH_EMAIL, DEV_AUTH_PASSWORD, hasSupabaseEnvironment } from "@/lib/env";
import { createSupabaseBrowserClient } from "@/lib/supabase-browser";
import { signUp } from "@/lib/api-client";
import { buildOAuthRedirectTo } from "@/lib/oauth";

function GoogleLogo() {
  return (
    <svg aria-hidden="true" width="18" height="18" viewBox="0 0 18 18">
      <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62Z" />
      <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.35 0-4.34-1.58-5.05-3.71H.94v2.33A9 9 0 0 0 9 18Z" />
      <path fill="#FBBC05" d="M3.95 10.71A5.41 5.41 0 0 1 3.67 9c0-.59.1-1.17.28-1.71V4.96H.94A9 9 0 0 0 0 9c0 1.45.34 2.82.94 4.04l3.01-2.33Z" />
      <path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.46.9 11.42 0 9 0A9 9 0 0 0 .94 4.96l3.01 2.33C4.66 5.16 6.65 3.58 9 3.58Z" />
    </svg>
  );
}

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
  const [googleLoading, setGoogleLoading] = useState(false);

  useEffect(() => {
    if (searchParams.get("error") === "oauth") {
      setError("Google sign in could not be completed. Try again or use email and password.");
    }
  }, [searchParams]);

  async function handleGoogleSignIn() {
    if (!hasSupabaseEnvironment()) {
      setError("Google sign in is only available when Supabase Auth is configured.");
      return;
    }

    setGoogleLoading(true);
    setError("");
    setSuccess("");

    const supabase = createSupabaseBrowserClient();
    const { error: oauthError } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: buildOAuthRedirectTo(searchParams.get("next") || "/dashboard"),
        queryParams: {
          prompt: "select_account",
        },
      },
    });

    if (oauthError) {
      setGoogleLoading(false);
      setError("Google sign in could not be started. Try again or use email and password.");
    }
  }

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
        disabled={googleLoading}
        icon={isSignUp ? <UserPlus size={16} aria-hidden="true" /> : <LogIn size={16} aria-hidden="true" />}
      >
        {isSignUp ? "Sign up" : "Sign in"}
      </Button>

      <div className="auth-divider" aria-hidden="true">
        <span />
        <strong>or</strong>
        <span />
      </div>

      <Button
        type="button"
        variant="secondary"
        className="google-auth-button"
        loading={googleLoading}
        disabled={loading}
        icon={<GoogleLogo />}
        onClick={handleGoogleSignIn}
      >
        Continue with Google
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
  const [bgImage, setBgImage] = useState<string>("");

  useEffect(() => {
    try {
      const lastBg = localStorage.getItem("markit_last_bg");
      const nextBg = lastBg === "/bg1.png" ? "/bg2.png" : "/bg1.png";
      setBgImage(nextBg);
      localStorage.setItem("markit_last_bg", nextBg);
    } catch (e) {
      // Fallback to random if localStorage fails
      const randomBg = Math.random() < 0.5 ? "/bg1.png" : "/bg2.png";
      setBgImage(randomBg);
    }
  }, []);

  return (
    <main 
      className="login-page"
      style={bgImage ? { backgroundImage: `linear-gradient(rgba(15, 23, 42, 0.35), rgba(15, 23, 42, 0.45)), url('${bgImage}')` } : undefined}
    >
      <section className="login-panel" aria-labelledby="login-title">
        <div style={{ textAlign: "center", marginBottom: "20px" }}>
          <img src="/favicon.png" alt="" width="80" height="45" style={{ objectFit: "contain", display: "block", margin: "0 auto 12px" }} />
          <p className="eyebrow" style={{ margin: 0 }}>MarkIt</p>
        </div>
        <div>
          <h1 id="login-title" style={{ textAlign: "center" }}>
            {isSignUp ? "Create your account" : "Sign in to MarkIt"}
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
