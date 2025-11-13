import streamlit as st
import pandas as pd

# Load GTFS (already uploaded in GitHub)
routes = pd.read_csv("routes.txt")
stops = pd.read_csv("stops.txt")
trips = pd.read_csv("trips.txt")
stop_times = pd.read_csv("stop_times.txt")

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Multan Public Transport Dashboard",
    layout="wide",
)

# ---------- CUSTOM CSS (Bootstrap-like UI) ----------
st.markdown("""
<style>
/* Title */
h1 {
    color: #0056b3;
    font-weight: 700;
}

/* Stats Cards */
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
.stat-label {
    font-size: 15px;
    color: #444;
}

/* Section headers */
.section-title {
    font-size: 26px;
    margin-top: 35px;
    color: #0056b3;
    font-weight: 600;
}

/* Table improvements */
table {
    font-size: 15px;
}

/* Action buttons */
.view-btn {
    background-color: #0d6efd;
    color: white;
    border-radius: 6px;
    padding: 6px 12px;
    text-decoration: none;
}
.view-btn:hover {
    background-color: #0b5ed7;
    color: white;
}

/* Center Messages */
.center-info {
    text-align:center;
    font-size:18px;
    color:#007bff;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)


# ---------- TITLE ----------
st.markdown("<h1>🚍 Multan Public Transport Dashboard</h1>", unsafe_allow_html=True)
st.write("Live GTFS Data • No Database Required • Powered by Punjab IT Board")
st.markdown("---")


# ---------- SUMMARY CARDS ----------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"<div class='stat-card'><div class='stat-number'>{len(routes)}</div><div class='stat-label'>Total Routes</div></div>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<div class='stat-card'><div class='stat-number'>{len(trips)}</div><div class='stat-label'>Total Trips</div></div>", unsafe_allow_html=True)

with col3:
    st.markdown(f"<div class='stat-card'><div class='stat-number'>{len(stops)}</div><div class='stat-label'>Total Stops</div></div>", unsafe_allow_html=True)

with col4:
    st.markdown(f"<div class='stat-card'><div class='stat-number'>{len(stop_times)}</div><div class='stat-label'>Stop Times</div></div>", unsafe_allow_html=True)


# ---------- ROUTES SECTION ----------
st.markdown("<div class='section-title'>📋 Routes List</div>", unsafe_allow_html=True)

# Add action buttons inside dataframe
def btn(label, route_id):
    return f"<a class='view-btn' href='?route={route_id}'>{label}</a>"

routes_display = routes.copy()
routes_display["Stops"] = routes_display["route_id"].apply(lambda r: btn("View Stops", r))
routes_display["Timings"] = routes_display["route_id"].apply(lambda r: btn("View Timings", r))

# Remove index
st.write(
    routes_display.to_html(escape=False, index=False),
    unsafe_allow_html=True
)


# ---------- ROUTE SELECTION (Stops + Timings Panels) ----------
query_params = st.query_params

if "route" in query_params:
    selected_route = query_params["route"]

    st.markdown(f"<div class='section-title'>🚏 Stops for Route: <b>{selected_route}</b></div>", unsafe_allow_html=True)

    # FILTER STOP SEQUENCE
    trip_ids = trips[trips["route_id"] == selected_route]["trip_id"]
    st_times_filtered = stop_times[stop_times["trip_id"].isin(trip_ids)]
    st_times_filtered = st_times_filtered.merge(stops, on="stop_id")

    # UNIQUE STOPS WITH IN/OUT TAG
    st_times_filtered["Direction"] = st_times_filtered["stop_sequence"].apply(
        lambda x: "Forward (F)" if x <= st_times_filtered["stop_sequence"].median() else "Backward (B)"
    )

    stops_table = st_times_filtered[["stop_name", "stop_lat", "stop_lon", "Direction"]].drop_duplicates()

    st.write(stops_table)

    st.markdown(f"<div class='section-title'>⏱ Stop Timings</div>", unsafe_allow_html=True)

    timings = st_times_filtered[[
        "stop_name", "arrival_time", "departure_time", "Direction"
    ]]

    st.write(timings)

