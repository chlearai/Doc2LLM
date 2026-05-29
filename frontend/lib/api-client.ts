"use client";

import { getApiBaseUrl } from "./env";
import type { ApiErrorDetail, Conversion, UserProfile } from "./types";

type ConversionList = {
  items: Conversion[];
  limit: number;
  offset: number;
};

export class ApiClientError extends Error {
  detail: ApiErrorDetail;
  status: number;

  constructor(status: number, detail: ApiErrorDetail) {
    super(detail.message);
    this.name = "ApiClientError";
    this.status = status;
    this.detail = detail;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiClientError(
      response.status,
      body?.detail ?? { code: "REQUEST_FAILED", message: "Request failed." },
    );
  }
  return body as T;
}

export function createApiClient(accessToken: string) {
  const baseUrl = getApiBaseUrl();
  const headers = {
    Authorization: `Bearer ${accessToken}`,
  };

  return {
    async me() {
      const response = await fetch(`${baseUrl}/auth/me`, { headers });
      return parseResponse<UserProfile>(response);
    },
    async listConversions() {
      const response = await fetch(`${baseUrl}/conversions`, { headers });
      return parseResponse<ConversionList>(response);
    },
    async uploadConversion(file: File) {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${baseUrl}/conversions`, {
        method: "POST",
        headers,
        body: formData,
      });
      return parseResponse<Conversion>(response);
    },
    async getConversion(id: string) {
      const response = await fetch(`${baseUrl}/conversions/${id}`, { headers });
      return parseResponse<Conversion>(response);
    },
    async getStatus(id: string) {
      const response = await fetch(`${baseUrl}/conversions/${id}/status`, { headers });
      return parseResponse<Pick<Conversion, "id" | "status" | "error_message" | "completed_at">>(response);
    },
    async getMarkdown(id: string) {
      const response = await fetch(`${baseUrl}/conversions/${id}/markdown`, { headers });
      return parseResponse<{ id: string; markdown: string }>(response);
    },
    async getDownloadUrl(id: string) {
      const response = await fetch(`${baseUrl}/conversions/${id}/download-url`, { headers });
      return parseResponse<{ id: string; download_url: string; expires_in: number }>(response);
    },
    async deleteConversion(id: string) {
      const response = await fetch(`${baseUrl}/conversions/${id}`, {
        method: "DELETE",
        headers,
      });
      return parseResponse<{ id: string; status: "DELETED" }>(response);
    },
    async getAdminStats() {
      const response = await fetch(`${baseUrl}/admin/stats`, { headers });
      return parseResponse<{
        total_users: number;
        total_converted_files: number;
        files_processed_today: number;
        failed_conversions: number;
        pending_conversions: number;
        system_health: string;
      }>(response);
    },
    async listAdminUsers(search?: string, limit = 20, offset = 0) {
      const q = new URLSearchParams();
      if (search) q.set("search", search);
      q.set("limit", limit.toString());
      q.set("offset", offset.toString());
      const response = await fetch(`${baseUrl}/admin/users?${q.toString()}`, { headers });
      return parseResponse<{ items: any[]; limit: number; offset: number }>(response);
    },
    async createAdminUser(email: string, fullName?: string, role = "user") {
      const response = await fetch(`${baseUrl}/admin/users`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ email, full_name: fullName, role }),
      });
      return parseResponse<any>(response);
    },
    async updateAdminUserStatus(userId: string, isActive: boolean) {
      const response = await fetch(`${baseUrl}/admin/users/${userId}/status`, {
        method: "PUT",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: isActive }),
      });
      return parseResponse<any>(response);
    },
    async updateAdminUserRole(userId: string, role: string) {
      const response = await fetch(`${baseUrl}/admin/users/${userId}/role`, {
        method: "PUT",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });
      return parseResponse<any>(response);
    },
    async listAdminConversions(params?: { status?: string; user_id?: string; file_type?: string; search?: string; limit?: number; offset?: number }) {
      const q = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([k, v]) => {
          if (v !== undefined) q.set(k, v.toString());
        });
      }
      const response = await fetch(`${baseUrl}/admin/conversions?${q.toString()}`, { headers });
      return parseResponse<{ items: Conversion[]; limit: number; offset: number }>(response);
    },
    async cancelAdminConversion(id: string) {
      const response = await fetch(`${baseUrl}/admin/conversions/${id}/cancel`, {
        method: "POST",
        headers,
      });
      return parseResponse<Conversion>(response);
    },
    async retryAdminConversion(id: string) {
      const response = await fetch(`${baseUrl}/admin/conversions/${id}/retry`, {
        method: "POST",
        headers,
      });
      return parseResponse<Conversion>(response);
    },
    async deleteAdminConversion(id: string) {
      const response = await fetch(`${baseUrl}/admin/conversions/${id}`, {
        method: "DELETE",
        headers,
      });
      return parseResponse<{ id: string; status: "DELETED" }>(response);
    },
    async getAdminLogs(level?: string, search?: string, limit = 20, offset = 0) {
      const q = new URLSearchParams();
      if (level) q.set("level", level);
      if (search) q.set("search", search);
      q.set("limit", limit.toString());
      q.set("offset", offset.toString());
      const response = await fetch(`${baseUrl}/admin/logs?${q.toString()}`, { headers });
      return parseResponse<{ items: any[]; limit: number; offset: number }>(response);
    },
    async getAdminSystemHealth() {
      const response = await fetch(`${baseUrl}/admin/system-health`, { headers });
      return parseResponse<{
        railway_converter: { status: string; message?: string };
        supabase_connection: { status: string; message?: string };
        conversion_queue: { status: string; message?: string };
        storage_write: { status: string; message?: string };
      }>(response);
    },
    async updateProfile(fullName: string) {
      const response = await fetch(`${baseUrl}/auth/me`, {
        method: "PUT",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: fullName }),
      });
      return parseResponse<UserProfile>(response);
    },
    async changePassword(password: string) {
      const response = await fetch(`${baseUrl}/auth/change-password`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      return parseResponse<{ message: string }>(response);
    },
    async deleteAccount() {
      const response = await fetch(`${baseUrl}/auth/account`, {
        method: "DELETE",
        headers,
      });
      return parseResponse<{ message: string }>(response);
    },
  };
}

export async function signUp(email: string, password: string, fullName: string) {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  return parseResponse<{ message: string }>(response);
}
