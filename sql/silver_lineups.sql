-- Silver Lineups Table
SELECT
    CAST(match_id AS INTEGER) as match_id,
    team_name,
    CAST(player_id AS INTEGER) as player_id,
    player_name,
    CAST(jersey_number AS INTEGER) as jersey_number
FROM read_parquet(?)
