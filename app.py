import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Multan Public Transport Dashboard", layout="wide")

# Load Data
@st.cache_data
def load_data():
    routes = pd.read_csv("routes.txt")
    stops = pd.read_csv("stops.txt")
    stop_times = pd.read_csv("stop_times.txt")
    trips = pd.read_csv("trips.txt")
    return routes, stops, stop_times, trips

routes, stops, stop_times, trips = load_data()

# Header
st.title("🚌 Multan Public Transport Dashboard")
st.caption("Live GTFS Data • Powered by Punjab IT Board")

# KPI section
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Routes", len(routes))
col2.metric("Total Trips", len(trips))
col3.metric("Total Stops", len(stops))
col4.metric("Stop Times Records", len(stop_times))

st.markdown("---")

# ROUTE LIST
st.header("📋 Routes List")

# Only show required columns
clean_routes = routes[["route_id", "route_short_name"]].copy()
clean_routes["Stops"] = ""
clean_routes["Timings"] = ""

# Display table row by row
for index, row in clean_routes.iterrows():
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    
    c1.write(row["route_id"])
    c2.write(row["route_short_name"])

    show_stops = c3.button("View Stops", key=f"stops_{index}")
    show_times = c4.button("View Timings", key=f"times_{index}")

    # SHOW STOPS ON MAP
    if show_stops:
        st.subheader(f"🗺 Stops for Route {row['route_id']}")
        route_trips = trips[trips["route_id"] == row["route_id"]]["trip_id"].unique()
        route_stop_times = stop_times[stop_times["trip_id"].isin(route_trips)]
        route_stops = stops[stops["stop_id"].isin(route_stop_times["stop_id"].unique())]

        # Create Map
        if len(route_stops) > 0:
            m = folium.Map(location=[route_stops["stop_lat"].mean(), route_stops["stop_lon"].mean()], zoom_start=12)

            for _, stop in route_stops.iterrows():
                folium.Marker(
                    [stop["stop_lat"], stop["stop_lon"]],
                    popup=stop["stop_name"],
                    icon=folium.Icon(color="blue")
                ).add_to(m)

            st_folium(m, width=700, height=500)
        else:
            st.warning("No stops found for this route.")

    # SHOW TIMINGS TABLE
    if show_times:
        st.subheader(f"⏱ Timings for Route {row['route_id']}")

        route_trips = trips[trips["route_id"] == row["route_id"]]["trip_id"].unique()
        selected_times = stop_times[stop_times["trip_id"].isin(route_trips)]

        merged = selected_times.merge(stops, on="stop_id", how="left")
        merged = merged[["stop_name", "arrival_time", "departure_time"]]

        st.dataframe(merged, use_container_width=True)

