# xG90 — AI Project Context

## Identity
Project: xG90
Purpose: Football data lakehouse with team tactical fingerprinting and Streamlit dashboard.

## Current Status
last_completed_step: 6
next_step: 7
blocker: none
notes: ""

---

## Stack
- Language: Python 3.11+
- Data source: statsbombpy (no auth needed)
- Storage: AWS S3, Parquet files, medallion architecture (bronze/silver/gold)
- Transform engine: DuckDB (reads/writes Parquet on S3 via httpfs extension)
- Orchestration: Prefect
- Dashboard: Streamlit
- Viz: Plotly, mplsoccer
- Deps: pyarrow, boto3, pandas, python-dotenv

## Architecture
StatsBomb API → ingest.py → S3/bronze/ (raw Parquet)
S3/bronze/ → transform.py (DuckDB SQL) → S3/silver/ (clean tables)
S3/silver/ → features.py (DuckDB SQL) → S3/gold/team_fingerprints/
S3/gold/ → Streamlit dashboard

## S3 Layer Definitions
bronze: raw StatsBomb Parquet, partitioned by competition_id/season_id/match_id
silver: cleaned typed tables — events, shots, pressures, carries, lineups
gold: team_fingerprints — one row per team x match, all tactical metrics

## Silver Table Schemas
events: match_id, team_id, team_name, player_id, player_name, type, period, minute, second, location_x, location_y
shots: match_id, player_id, xg, location_x, location_y, body_part, outcome, under_pressure
pressures: match_id, team_id, location_x, location_y, success(bool), minute
carries: match_id, player_id, start_x, start_y, end_x, end_y, distance, progressive(bool)
lineups: match_id, team_id, player_id, position_name, jersey_number

## Gold Table Schema
team_fingerprints: competition_id, season_id, match_id, team_id, team_name,
  ppda, press_height, press_success_rate, defensive_line_height,
  compactness, counter_attack_speed, high_turnover_rate, progressive_carry_rate

## Metric Definitions
ppda: opponent_passes / (pressures + tackles + interceptions) in opponent half. lower = more pressing.
press_height: avg location_y of all pressure events (0-80 scale)
press_success_rate: % of pressures where turnover occurs within 5 seconds
defensive_line_height: avg location_x of defensive actions in own half
compactness: std deviation of player locations from team centroid
counter_attack_speed: avg seconds from defensive action to next shot (transitions only)
high_turnover_rate: % of turnovers won in opponent final third (x > 80)
progressive_carry_rate: carries advancing 10+ yards toward goal / total carries

## Project Structure
90xg/
  .env
  .gitignore
  pyproject.toml
  Makefile
  GEMINI.md
  pipeline/
    ingest.py
    transform.py
    features.py
    orchestrate.py
  models/
    tactical.py
  sql/
    silver_events.sql
    silver_shots.sql
    silver_pressures.sql
    silver_carries.sql
    silver_lineups.sql
    gold_fingerprints.sql
  dashboard/
    app.py
    pages/
      01_team_overview.py
      02_match_analysis.py
      03_team_comparison.py
    components/
      radar_chart.py
      pitch_heatmap.py
      match_timeline.py
  tests/
    test_ingest.py
    test_transform.py
    test_features.py

## Env Variables Required
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET_NAME=90xg-lakehouse
BRONZE_PREFIX=bronze
SILVER_PREFIX=silver
GOLD_PREFIX=gold

## Makefile Targets
install: install all deps
check: verify imports + S3 connection
ingest: run pipeline/ingest.py
transform: run pipeline/transform.py
features: run pipeline/features.py
orchestrate: run pipeline/orchestrate.py (full Prefect flow)
run: streamlit run dashboard/app.py
test: pytest tests/

---

## Steps

### Step 1 — Scaffolding
Files to create: .gitignore, pyproject.toml, .env (from env template), config.py, scripts/check_setup.py, Makefile
config.py: load .env with python-dotenv, expose typed constants for all env vars
check_setup.py: verify all imports work, connect to S3 with boto3, list bucket, print pass/fail per check
done_when: `make check` passes all checks

### Step 2 — Ingest (Bronze)
Files to create: pipeline/ingest.py
Functions:
  ingest_competitions() → s3://bucket/bronze/competitions/competitions.parquet
  ingest_matches(competition_id, season_id) → s3://bucket/bronze/matches/competition_id={}/season_id={}/
  ingest_events(match_id) → s3://bucket/bronze/events/competition_id={}/season_id={}/match_id={}/
  ingest_lineups(match_id) → s3://bucket/bronze/lineups/match_id={}/
  ingest_freeze_frames(match_id) → s3://bucket/bronze/freeze_frames/match_id={}/
Rules:
  add _ingested_at timestamp and _source="statsbomb_open" to every file
  flatten all nested JSON before writing Parquet
  use pyarrow for serialization, boto3 for S3 upload
  start with competition_id=11 season_id=27 (La Liga 2015/16)
done_when: bronze layer populated on S3, queryable via DuckDB

### Step 3 — Transform (Silver)
Files to create: pipeline/transform.py, sql/silver_*.sql
Rules:
  configure DuckDB with httpfs extension and AWS credentials from config.py
  one SQL file per silver table (schemas defined above)
  write transform_all(competition_id, season_id) function
  add row count and null checks after each table write
  write silver tables back to S3 as Parquet
done_when: all 5 silver tables on S3 with correct types and no nulls on key columns

### Step 4 — Feature Engineering (Gold)
Files to create: pipeline/features.py, models/tactical.py, sql/gold_fingerprints.sql
Rules:
  compute all 8 metrics defined in Metric Definitions section
  output: one row per team x match
  write compute_fingerprints(competition_id, season_id) in models/tactical.py
  pipeline/features.py calls the model and writes to S3 gold layer
  validate: every team has a row for every match played
done_when: gold/team_fingerprints/ on S3, PPDA varies meaningfully across teams

### Step 5 — Orchestration (Prefect)
Files to create: pipeline/orchestrate.py
Rules:
  wrap each pipeline function as @task
  compose into @flow named pipeline_90xg
  task dependencies: ingest → transform → features
  retries=2, retry_delay_seconds=30 on all ingest tasks
  CLI args: --competition and --season
  entry: python -m pipeline.orchestrate --competition 11 --season 27
done_when: full flow runs from CLI, all tasks visible in Prefect UI at localhost:4200

### Step 6 — Dashboard (Streamlit)
Files to create: dashboard/app.py, dashboard/pages/01-03, dashboard/components/*
Page 01 team_overview:
  inputs: competition + season dropdown, team dropdown
  outputs: PPDA gauge (Plotly), pressure heatmap on mplsoccer pitch, key stats table
Page 02 match_analysis:
  inputs: match dropdown
  outputs: rolling PPDA line chart per minute, shot map on pitch with xG bubble sizes
Page 03 team_comparison:
  inputs: two team dropdowns
  outputs: Plotly radar chart of all 8 metrics, sortable ranking table of all teams
Rules:
  read all data from S3 gold layer via DuckDB
  cache S3 reads with @st.cache_data
  show "data last updated" timestamp from Parquet metadata
done_when: all 3 pages load and render without errors via `make run`

### Step 7 — Tests & Hardening
Files to create: tests/test_ingest.py, tests/test_transform.py, tests/test_features.py
Rules:
  test_ingest: mock S3 with moto, assert correct Parquet schemas
  test_transform: run SQL transforms on small fixture data, assert output shapes
  test_features: assert ppda > 0, press_success_rate between 0-1, no nulls in gold table
  run full pipeline on competition_id=16 (Champions League) to prove generalization
done_when: pytest passes, pipeline runs cleanly on 2 competitions

### Step 8 — README & Deploy
Files to create/update: README.md, CONTRIBUTING.md, LICENSE
README must include:
  project description
  architecture diagram (ASCII)
  tech stack badges
  setup instructions: clone → fill .env → make install → make ingest → make run
  screenshot of dashboard
  screenshot of Prefect UI
  live Streamlit Cloud URL
Deploy: Streamlit Cloud, add AWS credentials as Streamlit Secrets
done_when: repo is public, README is complete, live demo URL works
