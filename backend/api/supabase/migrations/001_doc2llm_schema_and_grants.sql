create extension if not exists pgcrypto;

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null,
    full_name text,
    role text not null default 'user',
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.conversions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    original_file_name text not null,
    file_type text not null,
    mime_type text,
    file_size_bytes bigint not null,
    file_size_mb numeric generated always as (round((file_size_bytes::numeric / 1048576), 2)) stored,
    markdown_storage_path text,
    status text not null,
    error_message text,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint conversions_status_check check (
        status in ('UPLOAD_RECEIVED', 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'DELETED')
    )
);

create table if not exists public.conversion_logs (
    id uuid primary key default gen_random_uuid(),
    conversion_id uuid not null references public.conversions(id) on delete cascade,
    level text not null,
    message text not null,
    created_at timestamptz not null default now(),
    constraint conversion_logs_level_check check (level in ('info', 'warning', 'error'))
);

create index if not exists conversions_user_created_idx
on public.conversions (user_id, created_at desc);

create index if not exists conversions_user_status_idx
on public.conversions (user_id, status);

create index if not exists conversion_logs_conversion_created_idx
on public.conversion_logs (conversion_id, created_at asc);

alter table public.profiles enable row level security;
alter table public.conversions enable row level security;
alter table public.conversion_logs enable row level security;

grant usage on schema public to service_role;
grant select, insert, update, delete on public.profiles to service_role;
grant select, insert, update, delete on public.conversions to service_role;
grant select, insert, update, delete on public.conversion_logs to service_role;
grant usage, select on all sequences in schema public to service_role;

alter default privileges in schema public
grant select, insert, update, delete on tables to service_role;

alter default privileges in schema public
grant usage, select on sequences to service_role;
