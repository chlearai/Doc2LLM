create table if not exists public.feature_usage (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    feature text not null,
    model text not null,
    tokens integer not null default 0,
    created_at timestamptz not null default now(),
    constraint feature_usage_tokens_check check (tokens >= 0)
);

create index if not exists feature_usage_user_idx
on public.feature_usage (user_id);

create index if not exists feature_usage_user_feature_idx
on public.feature_usage (user_id, feature);

alter table public.feature_usage enable row level security;

grant select, insert, update, delete on public.feature_usage to service_role;
grant usage, select on all sequences in schema public to service_role;
