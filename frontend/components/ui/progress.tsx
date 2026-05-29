import type { ConversionStatus } from "@/lib/types";

const copy: Record<ConversionStatus, string> = {
  UPLOAD_RECEIVED: "File received.",
  PENDING: "Waiting for a conversion slot.",
  PROCESSING: "Converting your file.",
  COMPLETED: "Conversion completed.",
  FAILED: "Conversion failed. Upload the file again or try a smaller document.",
  DELETED: "Conversion deleted.",
};

export function StatusRow({ status }: { status: ConversionStatus }) {
  return (
    <div className="status-row" data-status={status.toLowerCase()}>
      <span className="status-dot" aria-hidden="true" />
      <span>{copy[status]}</span>
    </div>
  );
}
