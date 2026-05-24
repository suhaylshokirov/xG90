-- Gold Team Fingerprints Table
-- This query calculates tactical metrics per team per match

WITH match_teams AS (
    -- Get unique team-match combinations
    SELECT DISTINCT match_id, team_name
    FROM raw_events
),

defensive_actions AS (
    -- Identify defensive actions (Pressures, Tackles, Interceptions, etc.)
    SELECT 
        match_id, 
        team_name, 
        location_x, 
        location_y,
        type,
        minute,
        second
    FROM raw_events
    WHERE type IN ('Pressure', 'Interception', 'Tackle', 'Foul Committed', 'Block')
),

opponent_passes AS (
    -- Identify passes by the opponent in their defensive 2/3 of the pitch
    -- StatsBomb pitch is 120 units long. Opponent defensive 2/3 is x < 80 for them.
    -- But raw_events has team_name. We need to join to find the "opponent".
    SELECT 
        e.match_id,
        mt.team_name as team_name, -- The team WE are calculating for
        e.team_name as pass_team, -- The team that made the pass
        e.location_x
    FROM raw_events e
    JOIN match_teams mt ON e.match_id = mt.match_id AND e.team_name != mt.team_name
    WHERE e.type = 'Pass' AND e.location_x < 80
),

ppda_calc AS (
    -- ppda = opponent_passes / defensive_actions in opponent half
    SELECT 
        mt.match_id,
        mt.team_name,
        COUNT(DISTINCT op.rowid) as opp_passes,
        COUNT(DISTINCT da.rowid) as def_actions,
        CAST(COUNT(DISTINCT op.rowid) AS FLOAT) / NULLIF(COUNT(DISTINCT da.rowid), 0) as ppda
    FROM match_teams mt
    LEFT JOIN (SELECT *, row_number() OVER () as rowid FROM opponent_passes) op ON mt.match_id = op.match_id AND mt.team_name = op.team_name
    LEFT JOIN (SELECT *, row_number() OVER () as rowid FROM defensive_actions) da ON mt.match_id = da.match_id AND mt.team_name = da.team_name AND da.location_x > 40 -- Actions in opponent's half
    GROUP BY 1, 2
),

press_metrics AS (
    SELECT 
        match_id,
        team_name,
        AVG(location_x) as press_height,
        -- High turnover: defensive action in final third (x > 80)
        CAST(COUNT(CASE WHEN location_x > 80 THEN 1 END) AS FLOAT) / NULLIF(COUNT(*), 0) as high_turnover_rate
    FROM defensive_actions
    WHERE type = 'Pressure'
    GROUP BY 1, 2
),

defensive_line AS (
    SELECT 
        match_id,
        team_name,
        AVG(location_x) as defensive_line_height
    FROM defensive_actions
    WHERE location_x < 60 -- Own half
    GROUP BY 1, 2
),

prog_carries AS (
    SELECT 
        c.match_id,
        e.team_name,
        CAST(COUNT(CASE WHEN (c.end_x - c.start_x) > 10 THEN 1 END) AS FLOAT) / NULLIF(COUNT(*), 0) as progressive_carry_rate
    FROM raw_carries c
    JOIN raw_events e ON c.match_id = e.match_id AND c.player_id = e.player_id AND e.type = 'Carry'
    GROUP BY 1, 2
)

SELECT 
    p.match_id,
    p.team_name,
    p.ppda,
    pm.press_height,
    pm.high_turnover_rate,
    dl.defensive_line_height,
    pc.progressive_carry_rate,
    -- Placeholders for more complex metrics
    0.5 as press_success_rate,
    0.5 as compactness,
    0.5 as counter_attack_speed
FROM ppda_calc p
LEFT JOIN press_metrics pm ON p.match_id = pm.match_id AND p.team_name = pm.team_name
LEFT JOIN defensive_line dl ON p.match_id = dl.match_id AND p.team_name = dl.team_name
LEFT JOIN prog_carries pc ON p.match_id = pc.match_id AND p.team_name = pc.team_name
