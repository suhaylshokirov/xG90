import plotly.graph_objects as go
import streamlit as st

def render_radar(team_metrics, avg_metrics, team_name):
    # Mapping metrics to human-readable labels
    labels = {
        'ppda': 'Pressing Intensity (PPDA)',
        'press_height': 'Press Height',
        'high_turnover_rate': 'High Turnovers',
        'defensive_line_height': 'Defensive Line',
        'progressive_carry_rate': 'Prog. Carries'
    }
    
    categories = list(labels.values())
    
    # Extract values in the same order as labels
    team_vals = [team_metrics[k] for k in labels.keys()]
    avg_vals = [avg_metrics[k] for k in labels.keys()]
    
    fig = go.Figure()

    # League Average Trace
    fig.add_trace(go.Scatterpolar(
        r=avg_vals,
        theta=categories,
        fill='toself',
        name='League Average',
        line_color='rgba(200, 200, 200, 0.5)',
        fillcolor='rgba(200, 200, 200, 0.2)'
    ))

    # Team Trace
    fig.add_trace(go.Scatterpolar(
        r=team_vals,
        theta=categories,
        fill='toself',
        name=team_name,
        line_color='#22c55e', # Professional Green
        fillcolor='rgba(34, 197, 94, 0.3)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max(team_vals), max(avg_vals)) * 1.2],
                gridcolor="rgba(255, 255, 255, 0.2)"
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        title=dict(
            text=f"Tactical DNA: {team_name}",
            font=dict(size=24, color="white")
        )
    )
    
    return fig
