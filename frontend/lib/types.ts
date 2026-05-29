export type ConversionStatus =
  | "UPLOAD_RECEIVED"
  | "PENDING"
  | "PROCESSING"
  | "COMPLETED"
  | "FAILED"
  | "DELETED";

export type UserProfile = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
};

export type Conversion = {
  id: string;
  status: ConversionStatus;
  original_file_name: string;
  file_type: string;
  file_size_bytes: number;
  markdown_storage_path: string | null;
  created_at: string;
  mime_type?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  user_id?: string;
  user_email?: string | null;
  user_full_name?: string | null;
};

export type ApiErrorDetail = {
  code: string;
  message: string;
  request_id?: string;
};
