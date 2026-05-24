import streamlit as st
import duckdb
import pandas as pd
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from settings import config
from dashboard.components.radar_chart import render_radar
from dashboard.components.ui_theme import apply_custom_style

st.title("Team Overview")
apply_custom_style()

@st.cache_resource
def get_con():
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='{config.AWS_REGION}';")
    con.execute(f"SET s3_access_key_id='{config.AWS_ACCESS_KEY_ID}';")
    con.execute(f"SET s3_secret_access_key='{config.AWS_SECRET_ACCESS_KEY}';")
    return con

con = get_con()
gold_path = f"s3://{config.S3_BUCKET_NAME}/gold/team_fingerprints/fingerprints.parquet"

try:
    # Robust data loading using Pandas/s3fs
    import s3fs
    fs = s3fs.S3FileSystem(key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)
    with fs.open(gold_path) as f:
        raw_df = pd.read_parquet(f, engine="pyarrow")
    
    # Filter by Season
    seasons = sorted(raw_df['season_id'].unique())
    selected_season = st.sidebar.selectbox("Season ID Context", seasons, index=len(seasons)-1)
    df = raw_df[raw_df['season_id'] == selected_season]
    
    # Selection
    teams = sorted(df['team_name'].unique())
    selected_team = st.selectbox("Select a Team", teams)
    
    # Calculate League Average for the selected season
    metrics_cols = ['ppda', 'press_height', 'high_turnover_rate', 'defensive_line_height', 'progressive_carry_rate']
    avg_metrics = df[metrics_cols].mean().to_dict()
    
    team_data = df[df['team_name'] == selected_team]
    team_metrics = team_data[metrics_cols].mean().to_dict()
    
    st.divider()
    
    # --- TOP ROW: DNA BARS ---
    st.subheader("Tactical DNA (Percent of League Average)")
    dna_cols = st.columns(len(metrics_cols))
    for i, col_name in enumerate(metrics_cols):
        with dna_cols[i]:
            val = team_metrics[col_name]
            avg = avg_metrics[col_name]
            pct_of_avg = (val / avg) * 100 if avg != 0 else 0
            
            st.metric(
                label=col_name.replace('_', ' ').title(), 
                value=f"{val:.1f}", 
                delta=f"{pct_of_avg-100:.1f}% vs Avg", 
                delta_color="normal"
            )

    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Tactical Style Analysis")
        # (Persona logic remains ...)
        style_desc = []
        if team_metrics['ppda'] < avg_metrics['ppda'] * 0.9:
            style_desc.append("**Aggressive Pressing**: Forces opponents into mistakes early.")
        elif team_metrics['ppda'] > avg_metrics['ppda'] * 1.1:
            style_desc.append("**Passive Block**: Prefers to defend space.")
            
        for s in style_desc: st.write(s)

        st.markdown("### Why the Radar?")
        st.info("""
        The radar chart is the industry standard because it shows **shape and balance**. 
        - A 'large' area means the team is active in multiple phases.
        - A 'skewed' area shows a team that specializes (e.g., all pressing, no carries).
        - It allows you to see the **Tactical Identity** in one glance.
        """)
        
    with col2:
        import plotly.express as px
        fig = render_radar(team_metrics, avg_metrics, selected_team)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Gray = League Average | Green = Selected Team")

except Exception as e:
    st.error(f"Could not load Gold data. Error: {e}")
