import { Badge } from "./ui/badge";
import { StatusRow } from "./ui/progress";
import type { ConversionStatus } from "@/lib/types";

export function ConversionStatusPanel({ status }: { status: ConversionStatus }) {
  return (
    <div className="status-panel">
      <div className="status-panel-heading">
        <span>Status</span>
        <Badge status={status} />
      </div>
      <StatusRow status={status} />
    </div>
  );
}
