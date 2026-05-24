-- Silver Events Table
SELECT
    CAST(match_id AS INTEGER) as match_id,
    CAST(team_id AS INTEGER) as team_id,
    team as team_name,
    CAST(player_id AS INTEGER) as player_id,
    player as player_name,
    type as type,
    CAST(period AS INTEGER) as period,
    CAST(minute AS INTEGER) as minute,
    CAST(second AS INTEGER) as second,
    CAST(split(replace(replace(location, '[', ''), ']', ''), ',')[1] AS FLOAT) as location_x,
    CAST(split(replace(replace(location, '[', ''), ']', ''), ',')[2] AS FLOAT) as location_y,
    possession_team as possession_team_name,
    play_pattern as play_pattern
FROM read_parquet(?)
WHERE type IS NOT NULL
