"use client";

import { ArrowUpFromLine, FileText } from "lucide-react";
import { useRef } from "react";
import { Button } from "./ui/button";

const supported = ".pdf,.docx,.pptx,.xlsx,.csv,.txt,.html";

export function UploadDropzone({
  file,
  disabled,
  onFile,
}: {
  file: File | null;
  disabled?: boolean;
  onFile: (file: File) => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  function handleFiles(files: FileList | null) {
    const nextFile = files?.item(0);
    if (nextFile) onFile(nextFile);
  }

  return (
    <div
      className="upload-dropzone"
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        if (!disabled) handleFiles(event.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        className="visually-hidden"
        type="file"
        accept={supported}
        onChange={(event) => handleFiles(event.target.files)}
        disabled={disabled}
      />
      <div className="upload-icon" aria-hidden="true">
        {file ? <FileText size={22} /> : <ArrowUpFromLine size={22} />}
      </div>
      <div>
        <h2>{file ? file.name : "Choose a file to convert"}</h2>
        <p>PDF, DOCX, PPTX, XLSX, CSV, TXT, and HTML are supported. PDF files can be up to 25 MB.</p>
      </div>
      <Button type="button" variant="secondary" disabled={disabled} onClick={() => inputRef.current?.click()}>
        Select file
      </Button>
    </div>
  );
}
