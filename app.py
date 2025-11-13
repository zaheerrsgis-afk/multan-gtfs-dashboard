import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Load CSV GTFS files
routes = pd.read_csv("routes.txt")
stops = pd.read_csv("stops.txt")
trips = pd.read_csv("trips.txt")
stop_times = pd.read_csv("stop_times.txt")

st.set_page_config(page_title="Multan Public Transport Dashboard", layout="wide")

# ------------------- CUSTOM CSS ---------------------
st.markdown("""
<style>

h1 {
    color: #0056b3;
    font-weight: 700;
}

.stat-card {
    background: #ffffff;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    text-align: center;
    border-left: 6px solid #0d6efd;
}

.stat-number {
    font-size: 36px;
    font-weight: 700;
    color: #0d6efd;
}

.section-title {
    font-size: 26px;
    margin-top: 35px;
    color: #0056b3;
    font-weight: 600;
}

.action-btn {
    background-color: #0056b3;
    padding: 8px 15px;
    color: white !important;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 500;
}
.action-btn:hover {
    background-color: #003f82;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# ------------------- HEADER ---------------------
st.markdown("<h1>🚍 Multan Public Transport Dashboard</h1>", unsafe_allow_html=True)
st.write("Live GTFS Data • No Database Required • Powered by Punjab IT Board")
st.markdown("---")

# ------------------- STATS CARDS ---------------------
col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"<div class='stat-card'><div class='stat-number'>{len(routes)}</div>Total Routes</div>", unsafe_allow_html=True)
col2.markdown(f"<div class='stat-card'><div class='stat-number'>{len(trips)}</div>Total Trips</div>", unsafe_allow_html=True)
col3.markdown(f"<div class='stat-card'><div class='stat-number'>{len(stops)}</div>Total Stops</div>", unsafe_allow_html=True)
col4.markdown(f"<div class='stat-card'><div class='stat-number'>{len(stop_times)}</div>Stop Timings</div>", unsafe_allow_html=True)

# ------------------- ROUTES LIST ---------------------
st.markdown("<div class='section-title'>📋 Routes List</div>", unsafe_allow_html=True)

def btn(label, route_id):
    return f"<a class='action-btn' href='?route={route_id}'>{label}</a>"

# Clean routes table
routes_table = pd.DataFrame()
routes_table["Route ID"] = routes["route_id"]
routes_table["Route Name"] = routes["route_long_name"]
routes_table["Stops"] = routes["route_id"].apply(lambda r: btn("View Stops", r))
routes_table["Timings"] = routes["route_id"].apply(lambda r: btn("View Timings", r))

st.write(routes_table.to_html(escape=False, index=False), unsafe_allow_html=True)

# ------------------- ROUTE SELECTED ---------------------
query = st.query_params

if "route" in query:
    r_id = query["route"]

    st.markdown(f"<div class='section-title'>🛑 Stops for Route: <b>{r_id}</b></div>", unsafe_allow_html=True)

    trip_ids = trips[trips["route_id"] == r_id]["trip_id"]

    df = stop_times[stop_times["trip_id"].isin(trip_ids)].merge(stops, on="stop_id")

    # Smart forward/backward detection
    median_seq = df["stop_sequence"].median()
    df["Direction"] = df["stop_sequence"].apply(
          lambda x: "Forward (F)" if x <= median_seq else "Backward (B)"
    )

    # ------------ CLEAN STOPS TABLE ------------
    stops_clean = df[["stop_name", "stop_lat", "stop_lon", "Direction"]].drop_duplicates()
    st.write(stops_clean)

    # ------------ MAP WITH ALL STOPS ------------
    st.markdown("<div class='section-title'>🗺️ Route Map</div>", unsafe_allow_html=True)
    
    m = folium.Map(location=[30.2, 71.5], zoom_start=12)

    for _, row in stops_clean.iterrows():
        folium.CircleMarker(
            location=[row["stop_lat"], row["stop_lon"]],
            radius=5,
            color="blue" if "Forward" in row["Direction"] else "red",
            fill=True,
        ).add_to(m)

    st_folium(m, width=1200, height=450)

    # ------------ CLEAN TIMINGS TABLE ------------
    st.markdown(f"<div class='section-title'>⏱ Stop Timings (Sequence Only)</div>", unsafe_allow_html=True)

    timings_clean = df[["stop_name", "Direction"]].drop_duplicates()
    st.write(timings_clean)
