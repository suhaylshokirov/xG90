-- Silver Carries Table
SELECT
    CAST(match_id AS INTEGER) as match_id,
    CAST(player_id AS INTEGER) as player_id,
    player as player_name,
    CAST(split(replace(replace(location, '[', ''), ']', ''), ',')[1] AS FLOAT) as start_x,
    CAST(split(replace(replace(location, '[', ''), ']', ''), ',')[2] AS FLOAT) as start_y,
    CAST(split(replace(replace(carry_end_location, '[', ''), ']', ''), ',')[1] AS FLOAT) as end_x,
    CAST(split(replace(replace(carry_end_location, '[', ''), ']', ''), ',')[2] AS FLOAT) as end_y,
    -- Distance can be calculated or taken if exists, but StatsBomb usually requires calculation
    -- We'll just take the coordinates for now
    (end_x - start_x) as delta_x,
    (end_y - start_y) as delta_y
FROM read_parquet(?)
WHERE type = 'Carry'
