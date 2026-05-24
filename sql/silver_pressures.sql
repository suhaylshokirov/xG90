-- Silver Pressures Table
SELECT
    CAST(match_id AS INTEGER) as match_id,
    CAST(team_id AS INTEGER) as team_id,
    team as team_name,
    CAST(split(replace(replace(location, '[', ''), ']', ''), ',')[1] AS FLOAT) as location_x,
    CAST(split(replace(replace(location, '[', ''), ']', ''), ',')[2] AS FLOAT) as location_y,
    CAST(minute AS INTEGER) as minute,
    CAST(second AS INTEGER) as second
FROM read_parquet(?)
WHERE type = 'Pressure'
