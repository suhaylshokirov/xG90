import streamlit as st

def apply_custom_style():
    st.markdown("""
    <style>
    /* Dark Glassmorphism Theme */
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
        color: #f8fafc;
    }
    
    /* Custom Card Design */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px 20px;
        border-radius: 12px;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #22c55e;
    }

    /* Professional Sidebar */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Button Styling */
    .stButton>button {
        background: linear-gradient(90deg, #22c55e, #16a34a);
        color: white;
        border: none;
        padding: 10px 25px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
        transform: scale(1.02);
    }

    /* Header effects */
    h1, h2, h3 {
        background: linear-gradient(90deg, #f8fafc, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    /* Table Glassmorphism */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)
