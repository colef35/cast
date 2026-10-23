-- CAST migration 002 — universal product profiles (SPEC §4.1) + workspaces (§4.2)
--
-- Phase 0 turns the single-product schema into the platform schema:
--   * product_profiles gains every SPEC §4.1 field, so ALL product specifics
--     (pitch/proof points, keywords, problem phrases, competitors, target
--     communities per platform, blocked communities, buying/relevance/reject
--     signals, per-channel search queries, feature map, voice profile,
--     guardrails) live in the profile row — nothing is hardcoded in code.
--   * a workspaces table lands the §4.2 tenancy shape: a user owns
--     workspaces, a workspace holds many profiles, and profiles/opportunities
--     stay scoped per user with row level security. workspace_id is nullable
--     so existing profiles keep working untouched (owner = user_id, as
--     before); new profiles can be attached to a workspace as the hosted
--     onboarding comes online.
--
-- Idempotent: safe to re-run. Apply in the Supabase SQL editor or via
-- scripts/setup_supabase.py-style rpc. Existing rows keep their values;
-- new columns default to empty, and the backend falls back to generic
-- defaults for any field a profile leaves empty.

-- ── Workspaces ──────────────────────────────────────────────────────────────
create table if not exists workspaces (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  created_at timestamptz default now()
);

alter table workspaces enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'workspaces'
      and policyname = 'Users own their workspaces'
  ) then
    create policy "Users own their workspaces"
      on workspaces
      for all
      using (auth.uid() = owner_id);
  end if;
end $$;

-- ── product_profiles: tenancy + SPEC §4.1 fields ────────────────────────────
alter table product_profiles
  add column if not exists workspace_id uuid references workspaces(id) on delete set null;

alter table product_profiles
  add column if not exists pricing_url text;

alter table product_profiles
  add column if not exists pitch_points text[] default '{}',
  add column if not exists proof_points text[] default '{}',
  add column if not exists problem_phrases text[] default '{}',
  add column if not exists competitors text[] default '{}',
  add column if not exists blocked_communities text[] default '{}',
  add column if not exists buying_signals text[] default '{}',
  add column if not exists domain_signals text[] default '{}',
  add column if not exists reject_signals text[] default '{}',
  add column if not exists free_tools text[] default '{}';

alter table product_profiles
  add column if not exists communities jsonb not null default '{}'::jsonb,
  add column if not exists relevance_signals jsonb not null default '{}'::jsonb,
  add column if not exists search_queries jsonb not null default '{}'::jsonb,
  add column if not exists feature_map jsonb not null default '[]'::jsonb,
  add column if not exists voice jsonb not null default '{}'::jsonb,
  add column if not exists guardrails jsonb not null default '{}'::jsonb;

alter table product_profiles
  add column if not exists default_feature text;

create index if not exists idx_product_profiles_workspace
  on product_profiles (workspace_id);

create index if not exists idx_product_profiles_user_updated
  on product_profiles (user_id, updated_at desc);
