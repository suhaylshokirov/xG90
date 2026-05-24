import streamlit as st
import pandas as pd
import duckdb
import sys
import os

# Add project root to sys.path so we can import 'settings' and 'pipeline'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from settings import config
from pipeline.orchestrate import pipeline_90xg
from dashboard.components.ui_theme import apply_custom_style

st.set_page_config(page_title="90xG — Tactical Intelligence", layout="wide")
apply_custom_style()

@st.cache_resource
def get_duckdb_con():
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='{config.AWS_REGION}';")
    con.execute(f"SET s3_access_key_id='{config.AWS_ACCESS_KEY_ID}';")
    con.execute(f"SET s3_secret_access_key='{config.AWS_SECRET_ACCESS_KEY}';")
    return con

@st.cache_data
def load_competitions():
    import s3fs
    fs = s3fs.S3FileSystem(key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)
    path = f"s3://{config.S3_BUCKET_NAME}/bronze/competitions/competitions.parquet"
    with fs.open(path) as f:
        df = pd.read_parquet(f, engine="pyarrow")
    return df

st.title("90xG — Tactical Intelligence")
st.markdown("""
Deep-dive tactical analysis platform powered by StatsBomb Open Data and a Medallion Lakehouse architecture.
""")

@st.cache_data
def load_matches(comp_id, season_id):
    con = get_duckdb_con()
    import s3fs
    fs = s3fs.S3FileSystem(key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)
    path = f"{config.S3_BUCKET_NAME}/bronze/matches/competition_id={comp_id}/season_id={season_id}/*.parquet"
    files = fs.glob(path)
    if not files: return pd.DataFrame()
    
    dfs = []
    for f_path in files:
        with fs.open(f"s3://{f_path}") as f:
            df_part = pd.read_parquet(f, engine="pyarrow")
            # Normalize types
            for col in ['competition_id', 'season_id', 'match_id', 'home_score', 'away_score']:
                if col in df_part.columns:
                    # Convert to numeric, filling NaNs with 0
                    df_part[col] = pd.to_numeric(df_part[col], errors='coerce').fillna(0).astype("int64")
            dfs.append(df_part)
    return pd.concat(dfs, ignore_index=True)

# Competition Selection
comps = load_competitions()
comp_options = comps.apply(lambda x: f"{x['competition_name']} ({x['season_name']})", axis=1).tolist()
selected_comp_name = st.selectbox("Select Competition to Analyze", comp_options)

selected_idx = comp_options.index(selected_comp_name)
row = comps.iloc[selected_idx]
c_id, s_id = row['competition_id'], row['season_id']

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Season Highlights")
    
    # Check if data exists in Gold layer
    gold_path = f"s3://{config.S3_BUCKET_NAME}/{config.GOLD_PREFIX}/team_fingerprints/fingerprints.parquet"
    
    try:
        # Use robust s3fs read for checking data readiness
        import s3fs
        fs = s3fs.S3FileSystem(key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)
        with fs.open(gold_path) as f:
            gold_df = pd.read_parquet(f, engine="pyarrow")
        
        # Filter for current competition/season
        comp_gold = gold_df[(gold_df['competition_id'] == c_id) & (gold_df['season_id'] == s_id)]
        data_ready = not comp_gold.empty
    except:
        data_ready = False

    if data_ready:
        st.success("Tactical Pipeline: Synchronized")
        
        st.markdown("### Top 5 Most Intense Pressing Teams")
        # Calculate Average PPDA (Lower is more intense)
        pressing_leaders = comp_gold.groupby('team_name').agg({
            'ppda': 'mean',
            'press_height': 'mean'
        }).sort_values('ppda', ascending=True).head(5)
        
        pressing_leaders.columns = ['Avg Pressing Intensity (PPDA)', 'Avg Press Height']
        st.dataframe(pressing_leaders.style.background_gradient(subset=['Avg Pressing Intensity (PPDA)'], cmap='Reds_r'), use_container_width=True)
        st.caption("Note: Rankings are based on averages from all available tactical data.")
    else:
        st.error("Data Pipeline: Offline")
        st.write("Tactical data for this season is not yet in the Lakehouse.")
        
        if st.button(f"Synchronize {selected_comp_name}"):
            with st.spinner("Processing..."):
                try:
                    pipeline_90xg(competition_id=c_id, season_id=s_id, limit=10)
                    st.success("Success!")
                    st.cache_data.clear() 
                    st.rerun()
                except Exception as e:
                    st.error(f"Pipeline failed: {e}")

with col2:
    st.subheader("Recent Results")
    if data_ready:
        matches = load_matches(c_id, s_id)
        if not matches.empty:
            display_df = matches[['match_date', 'home_team', 'home_score', 'away_score', 'away_team']]
            st.dataframe(display_df.sort_values('match_date', ascending=False), use_container_width=True)
    else:
        st.write("Awaiting data synchronization...")
