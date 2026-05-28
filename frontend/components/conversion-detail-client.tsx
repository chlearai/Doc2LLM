"use client";

import Link from "next/link";
import { Clipboard, Download, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiClientError, createApiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { formatDate, formatFileSize } from "@/lib/format";
import type { Conversion } from "@/lib/types";
import { MarkdownPreview } from "./markdown-preview";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { StatusRow } from "./ui/progress";

function readableError(error: unknown) {
  if (error instanceof ApiClientError) return error.detail.message;
  if (error instanceof Error) return error.message;
  return "Conversion could not be loaded.";
}

export function ConversionDetailClient({ id }: { id: string }) {
  const router = useRouter();
  const [conversion, setConversion] = useState<Conversion | null>(null);
  const [markdown, setMarkdown] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function withClient<T>(fn: (client: ReturnType<typeof createApiClient>) => Promise<T>) {
    const token = await getAccessToken();
    if (!token) throw new Error("Sign in again to view this conversion.");
    return fn(createApiClient(token));
  }

  async function loadDetail() {
    setLoading(true);
    setError("");
    try {
      const detail = await withClient((client) => client.getConversion(id));
      setConversion(detail);
      if (detail.status === "COMPLETED") {
        const result = await withClient((client) => client.getMarkdown(id));
        setMarkdown(result.markdown);
      }
    } catch (detailError) {
      setError(readableError(detailError));
    } finally {
      setLoading(false);
    }
  }

  async function copyMarkdown() {
    if (!markdown) return;
    await navigator.clipboard.writeText(markdown);
    setNotice("Markdown copied.");
  }

  function downloadMarkdown() {
    if (!markdown || !conversion) return;
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const stem = conversion.original_file_name.replace(/\.[^.]+$/, "");
    anchor.href = url;
    anchor.download = `${stem || "converted"}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
    setNotice("Download started.");
  }

  async function deleteConversion() {
    setError("");
    try {
      await withClient((client) => client.deleteConversion(id));
      router.replace("/history");
      router.refresh();
    } catch (deleteError) {
      setError(readableError(deleteError));
    }
  }

  useEffect(() => {
    loadDetail();
  }, [id]);

  if (loading) {
    return <section className="page-panel"><div className="skeleton-list" aria-label="Loading conversion" /></section>;
  }

  if (!conversion) {
    return (
      <section className="page-panel">
        <p className="message error-message">{error || "Conversion does not exist."}</p>
        <Link href="/history" className="text-link">Back to history</Link>
      </section>
    );
  }

  return (
    <section className="page-panel detail-panel">
      <div className="detail-header">
        <div>
          <Link href="/history" className="text-link">Back to history</Link>
          <h1>{conversion.original_file_name}</h1>
          <div className="detail-meta">
            <Badge status={conversion.status} />
            <span>{conversion.file_type.toUpperCase()}</span>
            <span>{formatFileSize(conversion.file_size_bytes)}</span>
            <span>{formatDate(conversion.created_at)}</span>
          </div>
        </div>
        <div className="preview-actions">
          <Button
            type="button"
            variant="secondary"
            onClick={copyMarkdown}
            disabled={!markdown}
            icon={<Clipboard size={15} aria-hidden="true" />}
          >
            Copy Markdown
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={downloadMarkdown}
            disabled={!markdown}
            icon={<Download size={15} aria-hidden="true" />}
          >
            Download .md
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={deleteConversion}
            icon={<Trash2 size={15} aria-hidden="true" />}
          >
            Delete
          </Button>
        </div>
      </div>

      <StatusRow status={conversion.status} />
      {conversion.error_message ? <p className="message error-message">{conversion.error_message}</p> : null}
      {error ? <p className="message error-message">{error}</p> : null}
      {notice ? <p className="message success-message">{notice}</p> : null}
      <MarkdownPreview markdown={markdown} />
    </section>
  );
}
