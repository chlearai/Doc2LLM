"use client";

import { useEffect, useState } from "react";
import { ApiClientError, createApiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import type { Conversion } from "@/lib/types";
import { ConversionTable } from "./conversion-table";
import { EmptyState } from "./empty-state";

function readableError(error: unknown) {
  if (error instanceof ApiClientError) return error.detail.message;
  if (error instanceof Error) return error.message;
  return "History could not be loaded.";
}

export function HistoryClient() {
  const [items, setItems] = useState<Conversion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function withClient<T>(fn: (client: ReturnType<typeof createApiClient>) => Promise<T>) {
    const token = await getAccessToken();
    if (!token) throw new Error("Sign in again to view history.");
    return fn(createApiClient(token));
  }

  async function loadHistory() {
    setLoading(true);
    setError("");
    try {
      const response = await withClient((client) => client.listConversions());
      setItems(response.items.filter((item) => item.status !== "DELETED"));
    } catch (historyError) {
      setError(readableError(historyError));
    } finally {
      setLoading(false);
    }
  }

  async function deleteConversion(id: string) {
    setError("");
    try {
      await withClient((client) => client.deleteConversion(id));
      setItems((existing) => existing.filter((item) => item.id !== id));
    } catch (deleteError) {
      setError(readableError(deleteError));
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  if (loading) {
    return <div className="skeleton-list" aria-label="Loading history" />;
  }

  return (
    <>
      {error ? <p className="message error-message">{error}</p> : null}
      {items.length ? (
        <ConversionTable conversions={items} onDelete={deleteConversion} />
      ) : (
        <EmptyState title="No conversion history">Convert a file from the dashboard to build your history.</EmptyState>
      )}
    </>
  );
}
