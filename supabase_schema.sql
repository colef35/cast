-- CAST schema — fresh installs.
-- Existing installs: apply supabase_migration_002_product_profiles.sql
-- instead (it adds the Phase 0 profile columns + workspaces idempotently).

-- Workspaces (SPEC §4.2): one user owns workspaces; a workspace holds many
-- product profiles; queues/scores/history hang off the profile.
create table workspaces (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  created_at timestamptz default now()
);

alter table workspaces enable row level security;

create policy "Users own their workspaces"
  on workspaces
  for all
  using (auth.uid() = owner_id);

create table product_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  workspace_id uuid references workspaces(id) on delete set null,
  name text not null,
  tagline text not null,
  description text not null,
  target_audience text not null,
  pain_point_solved text not null,
  url text,
  pricing_summary text,
  pricing_url text,
  keywords text[] default '{}',
  -- SPEC §4.1 profile fields
  pitch_points text[] default '{}',
  proof_points text[] default '{}',
  problem_phrases text[] default '{}',
  competitors text[] default '{}',
  communities jsonb not null default '{}'::jsonb,        -- platform → [community, …]
  blocked_communities text[] default '{}',
  buying_signals text[] default '{}',
  domain_signals text[] default '{}',
  relevance_signals jsonb not null default '{}'::jsonb,   -- channel → [phrase, …]
  reject_signals text[] default '{}',
  search_queries jsonb not null default '{}'::jsonb,      -- channel → [query, …]
  feature_map jsonb not null default '[]'::jsonb,         -- [{keywords:[…], feature:"…"}]
  default_feature text,
  free_tools text[] default '{}',
  voice jsonb not null default '{}'::jsonb,               -- {tone, example_posts, draft_templates}
  guardrails jsonb not null default '{}'::jsonb,          -- {forbidden_claims, avoid_topics, disclose_ai}
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table product_profiles enable row level security;

create policy "Users own their products"
  on product_profiles
  for all
  using (auth.uid() = user_id);

create table opportunities (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references product_profiles(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  channel text not null,
  source_url text not null,
  source_title text not null,
  source_body text not null,
  relevance_score float not null,
  roi_score float not null,
  draft text,
  status text not null default 'pending',
  created_at timestamptz default now(),
  acted_at timestamptz
);

alter table opportunities enable row level security;

create policy "Users own their opportunities"
  on opportunities
  for all
  using (auth.uid() = user_id);
