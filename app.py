import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Multan Public Transport Dashboard",
    layout="wide",
)

st.markdown(
    """
    <h1 style='text-align:center; color:#005be4;'>🚌 Multan Public Transport Dashboard</h1>
    <p style='text-align:center; font-size:18px;'>Live GTFS Data • No Database Required • Powered by Punjab IT Board</p>
    <br>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------
# LOAD GTFS FILES
# ------------------------------------------------------------
routes = pd.read_csv("routes.txt")
trips = pd.read_csv("trips.txt")
stops = pd.read_csv("stops.txt")
stop_times = pd.read_csv("stop_times.txt")

# ------------------------------------------------------------
# METRICS ROW
# ------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Routes", len(routes))
col2.metric("Total Trips", len(trips))
col3.metric("Total Stops", len(stops))
col4.metric("Stop Time Records", len(stop_times))

st.markdown("---")

# ------------------------------------------------------------
# ROUTES TABLE
# ------------------------------------------------------------
st.subheader("📋 Routes List")

clean_routes = routes[["route_id", "route_short_name", "route_long_name"]]

st.dataframe(clean_routes, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------
# ROUTE DETAILS (Stops + Timings)
# ------------------------------------------------------------
st.subheader("🔍 Route Explorer")

selected_route = st.selectbox("Choose a Route:", clean_routes["route_id"].unique())

route_row = routes[routes["route_id"] == selected_route].iloc[0]

st.markdown(
    f"""
    <h4 style='color:#005be4;'>Route: {route_row['route_short_name']}</h4>
    <p>{route_row['route_long_name']}</p>
    """,
    unsafe_allow_html=True
)

colA, colB = st.columns(2)

with colA:
    show_stops = st.button("📍 View Stops", use_container_width=True)

with colB:
    show_times = st.button("⏱ View Timings", use_container_width=True)

# ------------------------------------------------------------
# LOGIC TO FIND STOPS & TRIPS
# ------------------------------------------------------------
route_trips = trips[trips["route_id"] == selected_route]["trip_id"].unique()
stop_ids = stop_times[stop_times["trip_id"].isin(route_trips)]["stop_id"].unique()

route_stops = stops[stops["stop_id"].isin(stop_ids)]
route_times = stop_times[stop_times["trip_id"].isin(route_trips)]

# ------------------------------------------------------------
# SHOW MAP OF STOPS
# ------------------------------------------------------------
if show_stops:
    st.subheader("🗺 Stops on Map")

    if len(route_stops) > 0:
        # Create map
        m = folium.Map(
            location=[route_stops["stop_lat"].mean(), route_stops["stop_lon"].mean()],
            zoom_start=12
        )

        # Add markers
        for _, stop in route_stops.iterrows():
            folium.Marker(
                [stop["stop_lat"], stop["stop_lon"]],
                popup=stop["stop_name"],
                icon=folium.Icon(color="red")
            ).add_to(m)

        st_folium(m, width=700, height=500)

        # Also show table
        st.dataframe(route_stops[["stop_id", "stop_name"]], use_container_width=True)

    else:
        st.warning("No stops found for this route.")

# ------------------------------------------------------------
# SHOW TIMINGS LIST
# ------------------------------------------------------------
if show_times:
    st.subheader("⏱ Stop Timings")

    timings_table = route_times.merge(stops, on="stop_id", how="left")
    timings_table = timings_table[
        ["trip_id", "stop_id", "stop_name", "arrival_time", "departure_time"]
    ]

    st.dataframe(timings_table, use_container_width=True)
