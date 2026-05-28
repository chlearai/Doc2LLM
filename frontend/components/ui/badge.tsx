import type { ConversionStatus } from "@/lib/types";

const labels: Record<ConversionStatus, string> = {
  UPLOAD_RECEIVED: "Received",
  PENDING: "Waiting",
  PROCESSING: "Processing",
  COMPLETED: "Completed",
  FAILED: "Failed",
  DELETED: "Deleted",
};

export function Badge({ status }: { status: ConversionStatus }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{labels[status]}</span>;
}
