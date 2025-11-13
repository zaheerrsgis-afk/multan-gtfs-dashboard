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

# Make sure time columns are strings
for col in ["arrival_time", "departure_time"]:
    if col in stop_times.columns:
        stop_times[col] = stop_times[col].astype(str)

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

# keep route_id internally, but DON'T show in table
clean_routes = routes[["route_id", "route_short_name", "route_long_name"]]

# show only human-readable columns
st.dataframe(
    clean_routes[["route_short_name", "route_long_name"]],
    use_container_width=True
)

st.markdown("---")

# ------------------------------------------------------------
# SESSION STATE FIX FOR MAP HIDING ISSUE
# ------------------------------------------------------------
if "show_stops" not in st.session_state:
    st.session_state.show_stops = False

if "show_times" not in st.session_state:
    st.session_state.show_times = False

def show_stops_action():
    st.session_state.show_stops = True
    st.session_state.show_times = False

def show_times_action():
    st.session_state.show_times = True
    st.session_state.show_stops = False

# ------------------------------------------------------------
# ROUTE SELECTOR
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
    st.button("📍 View Stops", on_click=show_stops_action, use_container_width=True)

with colB:
    st.button("⏱ View Timings", on_click=show_times_action, use_container_width=True)

# ------------------------------------------------------------
# LOGIC TO FIND STOPS & TRIPS (WITH DIRECTION)
# ------------------------------------------------------------
# All trips for this route
route_trips = trips[trips["route_id"] == selected_route][["trip_id", "direction_id"]]

# All stop_times for those trips
route_stop_times = stop_times[stop_times["trip_id"].isin(route_trips["trip_id"])]

# Join to bring direction_id into stop_times
route_stop_times = route_stop_times.merge(route_trips, on="trip_id", how="left")

# Join with stops to get names and coordinates
route_full = route_stop_times.merge(stops, on="stop_id", how="left")

# Helper: convert 0/1 to Forward / Backward
def dir_label(x):
    if x == 0:
        return "Forward"
    elif x == 1:
        return "Backward"
    else:
        return "Unknown"

route_full["direction"] = route_full["direction_id"].apply(dir_label)

# ------------------------------------------------------------
# SHOW MAP OF STOPS (WITH FORWARD/BACKWARD)
# ------------------------------------------------------------
if st.session_state.show_stops:
    st.subheader("🗺 Stops on Map")

    # Unique stops per direction for this route
    route_stops = route_full[["stop_id", "stop_name", "stop_lat", "stop_lon", "direction"]].drop_duplicates()

    if len(route_stops) > 0:
        # Center map
        m = folium.Map(
            location=[route_stops["stop_lat"].mean(), route_stops["stop_lon"].mean()],
            zoom_start=12
        )

        # Color by direction
        def color_by_dir(d):
            return "blue" if d == "Forward" else "red"

        # Add markers
        for _, stop in route_stops.iterrows():
            folium.CircleMarker(
                [stop["stop_lat"], stop["stop_lon"]],
                radius=6,
                color=color_by_dir(stop["direction"]),
                fill=True,
                fill_color=color_by_dir(stop["direction"]),
                popup=f"{stop['stop_name']} ({stop['direction']})"
            ).add_to(m)

        st_folium(m, width=700, height=500)

        # Stops table with direction column
        st.dataframe(
            route_stops[["stop_id", "stop_name", "direction"]],
            use_container_width=True
        )

    else:
        st.warning("No stops found for this route.")

# ------------------------------------------------------------
# SHOW TIMINGS (WITHOUT departure_time, WITH direction)
# ------------------------------------------------------------
if st.session_state.show_times:
    st.subheader("⏱ Stop Timings")

    # Use route_full (already has direction + stop_name)
    timings_table = route_full[["trip_id", "stop_id", "stop_name", "arrival_time", "direction"]].copy()

    # Sort nicely
    timings_table = timings_table.sort_values(["direction", "trip_id", "arrival_time"])

    st.dataframe(timings_table, use_container_width=True)
