"use client";

export function MarkdownPreview({ markdown }: { markdown: string }) {
  if (!markdown) {
    return (
      <div className="markdown-preview empty-preview">
        Markdown preview appears after conversion completes.
      </div>
    );
  }

  return (
    <pre className="markdown-preview" aria-label="Markdown preview">
      <code>{markdown}</code>
    </pre>
  );
}
