import pandas as pd
import plotly.express as px
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Archerstarz Monster Invasion Dashboard",
    page_icon="🛡️",
    layout="wide",
)

# Custom Styling & Header
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF4B4B;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.2rem;
        border-radius: 0.5rem;
        border-left: 5px solid #FF4B4B;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="main-title">🛡️ Archerstarz Monster Invasion Analytics</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="sub-title">Interactive Player Portal & Performance Comparison Hub</p>',
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
  file_path = "Archerstarz Stats.xlsx"
  stats_df = pd.read_excel(file_path, sheet_name="Stats")
  if "Unnamed: 5" in stats_df.columns:
    stats_df = stats_df.drop(columns=["Unnamed: 5"])
  staging_df = pd.read_excel(file_path, sheet_name="Staging Data")
  return stats_df, staging_df


try:
  stats_df, staging_df = load_data()
except Exception as e:
  st.error(
      f"Error loading Excel file. Ensure 'Archerstarz Stats.xlsx' is in the"
      f" same directory. Details: {e}"
  )
  st.stop()

# Sidebar Navigation / Filters
st.sidebar.header("🎯 Player Selection")
players = sorted(stats_df["Name"].unique())
selected_player = st.sidebar.selectbox(
    "Choose your Player Profile:",
    players,
    index=players.index("B1gR3d") if "B1gR3d" in players else 0,
)

monsters = sorted(stats_df["Monster"].unique())
selected_monster = st.sidebar.selectbox(
    "Filter by Monster (for Leaderboards):", ["All Monsters"] + monsters
)

# Format large numbers helper
def format_score(val):
  if val >= 1e12:
    return f"{val / 1e12:.2f}T"
  elif val >= 1e9:
    return f"{val / 1e9:.2f}B"
  elif val >= 1e6:
    return f"{val / 1e6:.2f}M"
  else:
    return f"{val:,.0f}"


# --- TAB SETUP ---
tab1, tab2, tab3 = st.tabs(
    ["👤 My Player Dashboard", "📊 Comparative Charts", "🏆 Global Leaderboards"]
)

# ----------------------------------------------------
# TAB 1: PLAYER DASHBOARD
# ----------------------------------------------------
with tab1:
  st.subheader(f"Performance Overview: {selected_player}")

  player_data = stats_df[stats_df["Name"] == selected_player]

  # Calculate summary metrics for selected player
  total_score = player_data["Aggregated Score"].sum()
  avg_score = player_data["Average Score"].mean()
  best_score = player_data["Best"].max()
  total_attempts = player_data["Attempts"].sum()

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric("Total Aggregated Score", format_score(total_score))
  with col2:
    st.metric("Personal Best Hit", format_score(best_score))
  with col3:
    st.metric("Average Score per Boss", format_score(avg_score))
  with col4:
    st.metric("Total Attempts", f"{total_attempts}")

  st.markdown("---")

  col_left, col_right = st.columns([1.2, 1])

  with col_left:
    st.markdown("#### 🗡️ Performance Breakdown by Monster")
    display_df = player_data[
        [
            "Monster",
            "Best",
            "Average Score",
            "Aggregated Score",
            "Attempts",
            "Attack Frequency",
        ]
    ].copy()
    display_df["Best"] = display_df["Best"].apply(format_score)
    display_df["Average Score"] = display_df["Average Score"].apply(format_score)
    display_df["Aggregated Score"] = display_df["Aggregated Score"].apply(
        format_score
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)

  with col_right:
    st.markdown("#### 📊 Best Score vs Server Average")
    # Compute server average per monster
    server_avg = (
        stats_df.groupby("Monster")["Best"]
        .mean()
        .reset_index(name="Server Avg Best")
    )
    merged_comp = pd.merge(player_data, server_avg, on="Monster")

    fig_comp = px.bar(
        merged_comp,
        x="Monster",
        y=["Best", "Server Avg Best"],
        barmode="group",
        labels={"value": "Score", "variable": "Metric"},
        title="Your Best Scores vs Server Average",
    )
    fig_comp.update_layout(
        xaxis_tickangle=-35, margin=dict(l=20, r=20, t=40, b=20), height=350
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# ----------------------------------------------------
# TAB 2: COMPARATIVE CHARTS
# ----------------------------------------------------
with tab2:
  st.subheader("📊 Comparative Analysis & Benchmarks")
  st.markdown(
      "Compare individual scores and server-wide averages across all monster"
      " encounters."
  )

  chart_type = st.radio(
      "Select Chart Metric:",
      [
          "Player Best Scores by Monster",
          "Overall Average Score per Player",
          "Attack Frequency Distribution",
      ],
      horizontal=True,
  )

  if chart_type == "Player Best Scores by Monster":
    fig = px.bar(
        stats_df[stats_df["Best"] > 0],
        x="Name",
        y="Best",
        color="Monster",
        title="Best Scores Achieved by Players per Monster",
        labels={"Best": "Best Score", "Name": "Player"},
    )
    fig.update_layout(xaxis={'categoryorder': 'total descending'})
    st.plotly_chart(fig, use_container_width=True)

  elif chart_type == "Overall Average Score per Player":
    overall_avg = (
        stats_df.groupby("Name")["Average Score"].mean().reset_index()
    )
    overall_avg = overall_avg.sort_values(by="Average Score", ascending=False)

    fig = px.bar(
        overall_avg,
        x="Name",
        y="Average Score",
        title="Overall Average Score Across All Monsters per Player",
        color="Average Score",
        color_continuous_scale="Reds",
    )
    st.plotly_chart(fig, use_container_width=True)

  else:
    freq_df = (
        stats_df.groupby("Name")["Attack Frequency"].sum().reset_index()
    )
    freq_df = freq_df.sort_values(by="Attack Frequency", ascending=False)
    fig = px.bar(
        freq_df,
        x="Name",
        y="Attack Frequency",
        title="Total Attack Frequency per Player",
        color="Attack Frequency",
        color_continuous_scale="Blues",
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# TAB 3: GLOBAL LEADERBOARDS
# ----------------------------------------------------
with tab3:
  st.subheader("🏆 Server-Wide Leaderboards")

  if selected_monster == "All Monsters":
    # Aggregate across all monsters
    global_lb = (
        stats_df.groupby("Name")
        .agg(
            Total_Score=("Aggregated Score", "sum"),
            Max_Best=("Best", "max"),
            Avg_Score=("Average Score", "mean"),
            Total_Attempts=("Attempts", "sum"),
        )
        .reset_index()
    )
    global_lb = global_lb.sort_values(by="Total_Score", ascending=False)
    global_lb["Formatted Total Score"] = global_lb["Total_Score"].apply(
        format_score
    )
    global_lb["Formatted Max Best"] = global_lb["Max_Best"].apply(format_score)
    global_lb["Formatted Avg Score"] = global_lb["Avg_Score"].apply(
        format_score
    )

    st.markdown("#### Overall Global Ranking (All Monsters Combined)")
    display_global = global_lb[[
        "Name",
        "Formatted Total Score",
        "Formatted Max Best",
        "Formatted Avg Score",
        "Total_Attempts",
    ]]
    display_global.columns = [
        "Player Name",
        "Total Score",
        "Personal Best",
        "Average Score",
        "Total Attempts",
    ]
    st.dataframe(
        display_global.reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )
  else:
    # Filter by specific monster
    monster_lb = stats_df[stats_df["Monster"] == selected_monster].sort_values(
        by="Best", ascending=False
    )
    monster_lb["Formatted Best"] = monster_lb["Best"].apply(format_score)
    monster_lb["Formatted Avg"] = monster_lb["Average Score"].apply(format_score)

    st.markdown(f"#### Leaderboard for: {selected_monster}")
    display_monster = monster_lb[[
        "Name",
        "Formatted Best",
        "Formatted Avg",
        "Attempts",
        "Attack Frequency",
    ]]
    display_monster.columns = [
        "Player Name",
        "Best Score",
        "Average Score",
        "Attempts",
        "Attack Frequency",
    ]
    st.dataframe(
        display_monster.reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )