from pipeline.orchestrate import pipeline_90xg
import time

def warm_up_lakehouse():
    """
    Pre-processes the most popular/relevant leagues so the dashboard 
    is 'hot' and ready for users.
    """
    # List of (Comp_ID, Season_ID, Description)
    top_seasons = [
        (9, 281, "1. Bundesliga 2023/24"),
        (11, 27, "La Liga 2015/16"),
        (16, 4, "Champions League 2018/19"),
        (43, 106, "World Cup 2022")
    ]

    print(f"🚀 Starting Lakehouse Warm-up for {len(top_seasons)} seasons...")
    
    for c_id, s_id, desc in top_seasons:
        print(f"\n--- Warming up: {desc} ---")
        try:
            # We process 10 matches for each to give a good tactical sample
            pipeline_90xg(competition_id=c_id, season_id=s_id, limit=10)
            print(f"✅ {desc} is now hot!")
        except Exception as e:
            print(f"❌ Failed to warm up {desc}: {e}")
        
    print("\n🔥 All top leagues are now ready in the Gold layer!")

if __name__ == "__main__":
    warm_up_lakehouse()
