-- Silver Shots Table
SELECT
    CAST(match_id AS INTEGER) as match_id,
    team as team_name,
    CAST(player_id AS INTEGER) as player_id,
    player as player_name,
    CAST(minute AS INTEGER) as minute,
    CAST(second AS INTEGER) as second,
    CAST(shot_statsbomb_xg AS FLOAT) as xg,
    CAST(split(replace(replace(location, '[', ''), ']', ''), ',')[1] AS FLOAT) as location_x,
    CAST(split(replace(replace(location, '[', ''), ']', ''), ',')[2] AS FLOAT) as location_y,
    shot_body_part as body_part,
    shot_outcome as outcome,
    COALESCE(CAST(under_pressure AS BOOLEAN), false) as under_pressure
FROM read_parquet(?)
WHERE type = 'Shot'
