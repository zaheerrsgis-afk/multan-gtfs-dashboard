import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Multan GTFS Dashboard", layout="wide")

# -------------------------------------------------------------
# LOAD GTFS FILES
# -------------------------------------------------------------
@st.cache_data
def load_data():
    routes = pd.read_csv("routes.txt")
    stops = pd.read_csv("stops.txt")
    trips = pd.read_csv("trips.txt")
    stop_times = pd.read_csv("stop_times.txt")

    # Convert times safely
    for col in ["arrival_time", "departure_time"]:
        if col in stop_times:
            stop_times[col] = stop_times[col].astype(str)

    return routes, stops, trips, stop_times


routes, stops, trips, stop_times = load_data()

# -------------------------------------------------------------
# TITLE
# -------------------------------------------------------------
st.title("🚍 Multan Public Transport Dashboard")
st.caption("Live GTFS Viewer • Punjab IT Board • Multan Metro & Feeder Routes")

# -------------------------------------------------------------
# SUMMARY CARDS
# -------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Routes", len(routes))
col2.metric("Stops", len(stops))
col3.metric("Trips", len(trips))
col4.metric("Stop Timings", len(stop_times))

st.markdown("---")

# -------------------------------------------------------------
# ROUTE SELECTION
# -------------------------------------------------------------
st.header("📋 Select a Route")

route_list = dict(zip(routes["route_long_name"], routes["route_id"]))

selected_route_name = st.selectbox("Choose Route", list(route_list.keys()))
selected_route_id = route_list[selected_route_name]

# Filter data
route_trips = trips[trips.route_id == selected_route_id]
route_trip_ids = route_trips.trip_id.tolist()
route_stop_times = stop_times[stop_times.trip_id.isin(route_trip_ids)]

# Merge with stops
route_stops = route_stop_times.merge(stops, on="stop_id", how="left")

# Add direction name
route_stops["direction"] = route_stops["direction_id"].apply(lambda x: "Forward" if x == 0 else "Backward")

# Clean columns for STOP LIST
clean_stops = route_stops[["stop_id", "stop_name", "stop_lat", "stop_lon", "direction"]].drop_duplicates()

# Clean columns for TIMINGS (NO departure_time)
clean_times = route_stops[["stop_name", "arrival_time", "direction"]].copy()

# -------------------------------------------------------------
# DISPLAY STOPS LIST
# -------------------------------------------------------------
st.subheader(f"🚏 Stops for **{selected_route_name}**")

st.dataframe(clean_stops.sort_values(["direction", "stop_name"]), use_container_width=True)

# -------------------------------------------------------------
# MAP OF ROUTE STOPS
# -------------------------------------------------------------
st.subheader("🗺 Route Map")

# Center of stops
center_lat = clean_stops["stop_lat"].mean()
center_lon = clean_stops["stop_lon"].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

# Marker colors
def color_by_dir(d):
    return "blue" if d == "Forward" else "red"

# Add stops
for _, row in clean_stops.iterrows():
    folium.CircleMarker(
        location=[row["stop_lat"], row["stop_lon"]],
        radius=6,
        color=color_by_dir(row["direction"]),
        fill=True,
        fill_color=color_by_dir(row["direction"]),
        popup=f"{row['stop_name']} ({row['direction']})",
    ).add_to(m)

st_folium(m, width=900, height=500)

# -------------------------------------------------------------
# STOP TIMINGS (REMOVE departure_time)
# -------------------------------------------------------------
st.subheader(f"⏱ Stop Timings for **{selected_route_name}**")

clean_times = clean_times.sort_values(["direction", "arrival_time"])
st.dataframe(clean_times, use_container_width=True)

st.markdown("---")
st.caption("© Punjab IT Board • Multan GTFS Dashboard 2025")
