import streamlit as st
import duckdb
import pandas as pd
import sys
import os
import plotly.express as px
import plotly.graph_objects as go

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from settings import config
from dashboard.components.ui_theme import apply_custom_style

st.set_page_config(layout="wide")
st.title("Match Analysis")
apply_custom_style()

@st.cache_resource
def get_con():
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='{config.AWS_REGION}';")
    con.execute(f"SET s3_access_key_id='{config.AWS_ACCESS_KEY_ID}';")
    con.execute(f"SET s3_secret_access_key='{config.AWS_SECRET_ACCESS_KEY}';")
    return con

@st.cache_data
def load_match_list():
    con = get_con()
    import s3fs
    fs = s3fs.S3FileSystem(key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)
    path = f"{config.S3_BUCKET_NAME}/bronze/matches/*/*/*.parquet"
    files = fs.glob(path)
    if not files: return pd.DataFrame()

    dfs = []
    for f_path in files:
        with fs.open(f"s3://{f_path}") as f:
            df_part = pd.read_parquet(f, engine="pyarrow")
            if "match_id" in df_part.columns:
                df_part["match_id"] = df_part["match_id"].astype("int64")
            dfs.append(df_part)
    return pd.concat(dfs, ignore_index=True)

con = get_con()
matches_df = load_match_list()

# Define paths
silver_shots_path = f"s3://{config.S3_BUCKET_NAME}/silver/shots/shots.parquet"

if not matches_df.empty:
    import s3fs
    fs = s3fs.S3FileSystem(key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)

    try:
        with fs.open(silver_shots_path) as f:
            full_shots_df = pd.read_parquet(f, engine="pyarrow")
        
        # Only show matches that actually HAVE data
        available_mids = full_shots_df['match_id'].unique()
        ready_matches = matches_df[matches_df['match_id'].isin(available_mids)]
        
        if ready_matches.empty:
            st.info("No tactical data found. Please run the pipeline for this season.")
            st.stop()

        ready_matches['label'] = ready_matches.apply(lambda x: f"{x['match_date']} | {x['home_team']} {x['home_score']}-{x['away_score']} {x['away_team']}", axis=1)
        match_map = dict(zip(ready_matches['label'], ready_matches['match_id']))

        selected_label = st.selectbox("Select a Match to Analyze", list(match_map.keys()))
        mid = match_map[selected_label]

        match_info = ready_matches[ready_matches['match_id'] == mid].iloc[0]

        shots_df = full_shots_df[full_shots_df['match_id'] == mid].sort_values(['minute', 'second'])
        
        # --- MOMENTUM CHART ---
        st.subheader("Match Momentum (Cumulative xG)")
        
        fig_mom = go.Figure()
        for team in [match_info['home_team'], match_info['away_team']]:
            team_data = shots_df[shots_df['team_name'] == team].copy()
            team_data['cum_xg'] = team_data['xg'].cumsum()

            plot_data = pd.concat([
                pd.DataFrame({'minute': [0], 'cum_xg': [0]}),
                team_data[['minute', 'cum_xg']],
                pd.DataFrame({'minute': [95], 'cum_xg': [team_data['cum_xg'].max() if not team_data.empty else 0]})
            ])

            fig_mom.add_trace(go.Scatter(
                x=plot_data['minute'], y=plot_data['cum_xg'],
                mode='lines', name=team,
                line_shape='hv',
                line=dict(width=3)
            ))

        fig_mom.update_layout(
            height=300, 
            xaxis_title="Minute", yaxis_title="Expected Goals (xG)",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        )
        st.plotly_chart(fig_mom, use_container_width=True)

        st.divider()

        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.subheader("Shot Map")
            
            # --- PRO FIX: Create a 2-sided pitch view ---
            plot_shots = shots_df.copy()
            away_team = match_info['away_team']
            
            # Flip coordinates for Away Team
            plot_shots.loc[plot_shots['team_name'] == away_team, 'location_x'] = 120 - plot_shots.loc[plot_shots['team_name'] == away_team, 'location_x']
            plot_shots.loc[plot_shots['team_name'] == away_team, 'location_y'] = 80 - plot_shots.loc[plot_shots['team_name'] == away_team, 'location_y']

            fig_pitch = px.scatter(
                plot_shots, x="location_x", y="location_y", 
                size="xg", color="team_name",
                hover_data=["player_name", "outcome", "xg"],
                color_discrete_map={match_info['home_team']: "#22c55e", match_info['away_team']: "#ef4444"}
            )
            
            # Draw Pitch Lines
            fig_pitch.add_shape(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color="white", width=2))
            fig_pitch.add_shape(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color="white", width=2))
            fig_pitch.add_shape(type="circle", x0=51, y0=31, x1=69, y1=49, line=dict(color="white", width=2))
            fig_pitch.add_shape(type="rect", x0=0, y0=18, x1=18, y1=62, line=dict(color="white", width=1))
            fig_pitch.add_shape(type="rect", x0=102, y0=18, x1=120, y1=62, line=dict(color="white", width=1))
            # Visual Goal Indicators
            fig_pitch.add_shape(type="line", x0=0, y0=36, x1=0, y1=44, line=dict(color="#ef4444", width=5))
            fig_pitch.add_shape(type="line", x0=120, y0=36, x1=120, y1=44, line=dict(color="#22c55e", width=5))

            fig_pitch.update_layout(
                xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-5, 125]),
                yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-5, 85]),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(30, 41, 59, 0.5)",
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig_pitch, use_container_width=True)

        with col2:
            st.subheader("Shot Performance")
            summary = shots_df.groupby('team_name').agg({
                'xg': 'sum',
                'match_id': 'count'
            }).rename(columns={'match_id': 'Shots', 'xg': 'Total xG'})
            summary['xG per Shot'] = summary['Total xG'] / summary['Shots']
            st.table(summary.style.format("{:.2f}", subset=['Total xG', 'xG per Shot']))
            
            st.info("The pitch map now shows a realistic match view: **Away team attacks the left goal, Home team attacks the right.**")
            
    except Exception as e:
        st.error(f"Error loading match data: {e}")
else:
    st.info("No matches found. Run the pipeline first!")
