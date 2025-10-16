-- Schema
create schema if not exists korastats;
set search_path = korastats, public;

-- Reference tables
create table if not exists countries (
  id int primary key,
  name text not null
);

create table if not exists organizers (
  id int primary key,
  name text not null,
  country_id int references countries(id)
);

create table if not exists age_groups (
  id int primary key,
  name text not null
);

create table if not exists tournaments (
  id int primary key,
  name text not null,
  gender text,
  organizer_id int references organizers(id),
  age_group_id int references age_groups(id)
);

create table if not exists seasons (
  id int primary key,
  name text,
  gender text,
  nature text,
  tournament_id int references tournaments(id),
  start_date date,
  end_date date
);

create table if not exists teams (
  id int primary key,
  name text,
  logo text
);

create table if not exists stadiums (
  id int primary key,
  name text
);

create table if not exists referees (
  id int primary key,
  name text,
  dob date,
  nationality_id int references countries(id)
);

create table if not exists assistants (
  id int primary key,
  name text,
  gender text,
  dob date,
  nationality_id int references countries(id)
);

create table if not exists matches (
  id int primary key,
  tournament_id int references tournaments(id),
  season_id int references seasons(id),
  round int,
  stadium_id int references stadiums(id),
  date_time timestamp,
  last_update timestamp,
  score_home int,
  score_away int,
  status_id int,
  status_name text
);

-- Players & lineups
create table if not exists players (
  id int primary key,
  name text,
  nickname text,
  dob date,
  primary_position_id int,
  primary_position_name text,
  secondary_position_id int,
  secondary_position_name text
);

create table if not exists lineups (
  id bigserial primary key,
  match_id int references matches(id) on delete cascade,
  team_id int references teams(id),
  player_id int references players(id),
  shirt_number int,
  role text check (role in ('starter','sub')),
  side text check (side in ('home','away'))
);

-- Event lookups
create table if not exists event_categories (
  id int primary key,
  name text
);

create table if not exists event_types (
  id int primary key,
  name text
);

create table if not exists event_results (
  id int primary key,
  name text
);

create table if not exists body_parts (
  id int primary key,
  name text
);

-- Events
create table if not exists events (
  id bigserial primary key,
  match_id int references matches(id) on delete cascade,
  team_id int references teams(id),
  player_id int references players(id),
  nickname text,
  shirt_number int,
  half int,
  minute int,
  second int,
  msec numeric,
  time_in_sec numeric,
  x int,
  y int,
  category_id int references event_categories(id),
  event_id int references event_types(id),
  result_id int references event_results(id),
  guid text,
  guid_ref text,
  extra text,
  extra_id int,
  body_part_id int references body_parts(id)
);

-- Simple derived metrics table (example)
create table if not exists metrics_player_match (
  id bigserial primary key,
  match_id int references matches(id) on delete cascade,
  player_id int references players(id),
  team_id int references teams(id),
  minutes_played int,
  shots int,
  goals int,
  assists int,
  computed_at timestamptz default now()
);

-- Helpful indexes
create index if not exists idx_events_match_id on events(match_id);
create index if not exists idx_lineups_match_id on lineups(match_id);
create index if not exists idx_metrics_player_match on metrics_player_match(match_id, player_id);

reset search_path;