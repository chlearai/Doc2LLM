"use client";

import Link from "next/link";
import { Check, Clipboard, Download, RotateCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ApiClientError, createApiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import type { Conversion } from "@/lib/types";
import { ConversionTable } from "./conversion-table";
import { EmptyState } from "./empty-state";
import { MarkdownPreview } from "./markdown-preview";
import { UploadDropzone } from "./upload-dropzone";
import { Button } from "./ui/button";
import { StatusRow } from "./ui/progress";

const allowedExtensions = ["pdf", "docx", "pptx", "xlsx", "csv", "txt", "html"];
const pdfMaxBytes = 25 * 1024 * 1024;

function extensionFor(file: File) {
  return file.name.split(".").pop()?.toLowerCase() ?? "";
}

function readableError(error: unknown) {
  if (error instanceof ApiClientError) return error.detail.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong. Try again.";
}

export function DashboardClient() {
  const [file, setFile] = useState<File | null>(null);
  const [current, setCurrent] = useState<Conversion | null>(null);
  const [recent, setRecent] = useState<Conversion[]>([]);
  const [markdown, setMarkdown] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  const canConvert = useMemo(() => Boolean(file && !loading), [file, loading]);

  async function withClient<T>(fn: ReturnType<typeof createApiClient> extends infer C ? (client: C) => Promise<T> : never) {
    const token = await getAccessToken();
    if (!token) throw new Error("Sign in again before converting files.");
    return fn(createApiClient(token) as never);
  }

  async function loadRecent() {
    const list = await withClient((client) => client.listConversions());
    setRecent(list.items.filter((item) => item.status !== "DELETED"));
  }

  useEffect(() => {
    loadRecent().catch(() => undefined);
  }, []);

  function selectFile(nextFile: File) {
    const extension = extensionFor(nextFile);
    setError("");
    setNotice("");
    setMarkdown("");
    setCurrent(null);

    if (!allowedExtensions.includes(extension)) {
      setFile(null);
      setError("This file type is not supported. Choose PDF, DOCX, PPTX, XLSX, CSV, TXT, or HTML.");
      return;
    }
    if (nextFile.size === 0) {
      setFile(null);
      setError("The file is empty. Choose a file with content and try again.");
      return;
    }
    if (extension === "pdf" && nextFile.size > pdfMaxBytes) {
      setFile(null);
      setError("PDF is too large. PDF files can be up to 25 MB. Choose a smaller file and try again.");
      return;
    }

    setFile(nextFile);
  }

  async function convertFile() {
    if (!file) return;
    setLoading(true);
    setError("");
    setNotice("");
    setMarkdown("");

    try {
      const created = await withClient((client) => client.uploadConversion(file));
      setCurrent(created);
      await loadRecent();

      const status = await withClient((client) => client.getStatus(created.id));
      setCurrent((existing) => (existing ? { ...existing, ...status } : created));

      if (status.status === "COMPLETED") {
        const result = await withClient((client) => client.getMarkdown(created.id));
        setMarkdown(result.markdown);
        setNotice("Markdown is ready.");
      }
      if (status.status === "FAILED") {
        setError(status.error_message || "Conversion failed. Upload the file again or try a smaller document.");
      }
      await loadRecent();
    } catch (conversionError) {
      setError(readableError(conversionError));
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
    if (!markdown || !current) return;
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const stem = current.original_file_name.replace(/\.[^.]+$/, "");
    anchor.href = url;
    anchor.download = `${stem || "converted"}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
    setNotice("Download started.");
  }

  return (
    <div className="dashboard-grid">
      <section className="workspace-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Conversion workspace</p>
            <h1>Convert files into Markdown</h1>
          </div>
          <Button type="button" onClick={convertFile} disabled={!canConvert} loading={loading}>
            Convert file
          </Button>
        </div>

        <UploadDropzone file={file} disabled={loading} onFile={selectFile} />

        {current ? (
          <div className="status-strip">
            <StatusRow status={current.status} />
            <Link href={`/conversions/${current.id}`}>Open detail</Link>
          </div>
        ) : null}

        {error ? <p className="message error-message">{error}</p> : null}
        {notice ? <p className="message success-message">{notice}</p> : null}
        <p className="trust-note">Source files are deleted after conversion, failure, or timeout.</p>

        <div className="preview-heading">
          <h2>Markdown preview</h2>
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
          </div>
        </div>
        <MarkdownPreview markdown={markdown} />
      </section>

      <aside className="side-panel">
        <div className="side-heading">
          <h2>Recent conversions</h2>
          <Button
            type="button"
            variant="ghost"
            onClick={() => loadRecent()}
            icon={<RotateCw size={15} aria-hidden="true" />}
          >
            Refresh
          </Button>
        </div>
        {recent.length ? (
          <ConversionTable conversions={recent.slice(0, 5)} />
        ) : (
          <EmptyState title="No recent conversions">Convert a file to see it here.</EmptyState>
        )}
        {markdown ? (
          <div className="ready-note">
            <Check size={15} aria-hidden="true" />
            Markdown output is stored separately from the source file.
          </div>
        ) : null}
      </aside>
    </div>
  );
}
