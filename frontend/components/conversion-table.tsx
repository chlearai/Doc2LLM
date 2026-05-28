"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import { formatDate, formatFileSize } from "@/lib/format";
import type { Conversion } from "@/lib/types";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";

export function ConversionTable({
  conversions,
  onDelete,
}: {
  conversions: Conversion[];
  onDelete?: (id: string) => void;
}) {
  return (
    <div className="table-wrap">
      <table className="conversion-table">
        <thead>
          <tr>
            <th>File</th>
            <th>Status</th>
            <th>Size</th>
            <th>Created</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {conversions.map((conversion) => (
            <tr key={conversion.id}>
              <td>
                <Link href={`/conversions/${conversion.id}`} className="file-link">
                  {conversion.original_file_name}
                </Link>
                <span>{conversion.file_type.toUpperCase()}</span>
              </td>
              <td>
                <Badge status={conversion.status} />
              </td>
              <td>{formatFileSize(conversion.file_size_bytes)}</td>
              <td>{formatDate(conversion.created_at)}</td>
              <td>
                {onDelete ? (
                  <Button
                    type="button"
                    variant="ghost"
                    aria-label={`Delete ${conversion.original_file_name}`}
                    icon={<Trash2 size={15} aria-hidden="true" />}
                    onClick={() => onDelete(conversion.id)}
                  >
                    Delete
                  </Button>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
