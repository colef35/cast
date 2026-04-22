create table product_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  tagline text not null,
  description text not null,
  target_audience text not null,
  pain_point_solved text not null,
  url text,
  pricing_summary text,
  keywords text[] default '{}',
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
