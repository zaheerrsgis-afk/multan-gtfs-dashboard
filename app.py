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
    <p style='text-align:center; font-size:18px;'>Live GTFS Data • Powered by Punjab IT Board</p>
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

# Make sure time columns are strings (avoid parsing issues)
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
col4.metric("Stop Timings", len(stop_times))

st.markdown("---")

# ------------------------------------------------------------
# ALL STOPS MAP (GLOBAL VIEW)
# ------------------------------------------------------------
st.subheader("🗺️ All Stops (Map View)")

if not stops.empty:
    # Center map on mean of all stops
    center_lat = stops["stop_lat"].mean()
    center_lon = stops["stop_lon"].mean()

    m_all = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    for _, s in stops.iterrows():
        folium.CircleMarker(
            [s["stop_lat"], s["stop_lon"]],
            radius=3,
            color="#007bff",
            fill=True,
            fill_color="#007bff",
            popup=f"{s['stop_name']}"
        ).add_to(m_all)

    st_folium(m_all, width=900, height=450)
else:
    st.warning("No stops found in GTFS data.")

st.markdown("---")

# ------------------------------------------------------------
# ROUTES TABLE (CORRECT ATTRIBUTES)
# ------------------------------------------------------------
st.subheader("📋 Routes List")

# We keep route_id internally but show public-friendly columns
# Route Name  = route_long_name
# Short Code  = route_short_name
# Description = route_desc (if available)
display_cols = []

if "route_long_name" in routes.columns:
    display_cols.append("route_long_name")
if "route_short_name" in routes.columns:
    display_cols.append("route_short_name")
if "route_desc" in routes.columns:
    display_cols.append("route_desc")

# For internal logic, we still keep route_id
clean_routes = routes[["route_id", "route_short_name", "route_long_name"]].copy()

# Build public display dataframe
if display_cols:
    display_routes = routes[display_cols].copy()

    # Rename for nicer headings
    rename_map = {}
    if "route_long_name" in display_cols:
        rename_map["route_long_name"] = "Route Name"
    if "route_short_name" in display_cols:
        rename_map["route_short_name"] = "Short Code"
    if "route_desc" in display_cols:
        rename_map["route_desc"] = "Description"

    display_routes = display_routes.rename(columns=rename_map)

    st.dataframe(display_routes, use_container_width=True)
else:
    st.info("No suitable route attributes found to display (check routes.txt).")

st.markdown("---")

# ------------------------------------------------------------
# SESSION STATE FOR TOGGLES (MAP HIDING FIX)
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
# ROUTE EXPLORER (WITH FORWARD/BACKWARD)
# ------------------------------------------------------------
st.subheader("🔍 Route Explorer")

# Dropdown uses route_id internally, but we show short_name + long_name in label
route_options = []
for _, r in clean_routes.iterrows():
    label = f"{r['route_short_name']} – {r['route_long_name']}"
    route_options.append((label, r["route_id"]))

# Streamlit needs just labels; we map back to route_id
labels = [x[0] for x in route_options]
selected_label = st.selectbox("Choose a Route:", labels)
selected_route = dict(route_options)[selected_label]

# Get the row of selected route
route_row = routes[routes["route_id"] == selected_route].iloc[0]

st.markdown(
    f"""
    <h4 style='color:#005be4;'>Route: {route_row.get('route_short_name','')}</h4>
    <p>{route_row.get('route_long_name','')}</p>
    """,
    unsafe_allow_html=True
)

colA, colB = st.columns(2)

with colA:
    st.button("📍 View Stops (Forward / Backward)", on_click=show_stops_action, use_container_width=True)

with colB:
    st.button("⏱ View Stop Timings (Forward / Backward)", on_click=show_times_action, use_container_width=True)

# ------------------------------------------------------------
# LOGIC TO FIND STOPS & TRIPS (WITH DIRECTION)
# ------------------------------------------------------------
# All trips for the selected route
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
# SHOW MAP OF STOPS (PER ROUTE, WITH FORWARD/BACKWARD COLORS)
# ------------------------------------------------------------
if st.session_state.show_stops:
    st.subheader("🗺️ Route Stops (Forward / Backward)")

    route_stops = route_full[
        ["stop_id", "stop_name", "stop_lat", "stop_lon", "direction"]
    ].drop_duplicates()

    if len(route_stops) > 0:
        m = folium.Map(
            location=[route_stops["stop_lat"].mean(), route_stops["stop_lon"].mean()],
            zoom_start=12
        )

        def color_by_dir(d):
            return "blue" if d == "Forward" else "red"

        for _, stop in route_stops.iterrows():
            folium.CircleMarker(
                [stop["stop_lat"], stop["stop_lon"]],
                radius=6,
                color=color_by_dir(stop["direction"]),
                fill=True,
                fill_color=color_by_dir(stop["direction"]),
                popup=f"{stop['stop_name']} ({stop['direction']})"
            ).add_to(m)

        st_folium(m, width=900, height=500)

        # Stops table with separate Forward/Backward column
        st.dataframe(
            route_stops[["stop_name", "direction"]],
            use_container_width=True
        )
    else:
        st.warning("No stops found for this route.")

# ------------------------------------------------------------
# SHOW STOP TIMINGS (ARRIVAL ONLY, WITH DIRECTION)
# ------------------------------------------------------------
if st.session_state.show_times:
    st.subheader("⏱ Stop Timings (Forward / Backward)")

    if len(route_full) == 0:
        st.warning("No timings found for this route.")
    else:
        timings_table = route_full[
            ["direction", "trip_id", "stop_name", "arrival_time"]
        ].copy()

        # Sort: Forward first, then Backward, ordered by trip and time
        timings_table = timings_table.sort_values(
            ["direction", "trip_id", "arrival_time"]
        )

        # Nicer column names
        timings_table = timings_table.rename(columns={
            "direction": "Direction",
            "trip_id": "Trip",
            "stop_name": "Stop",
            "arrival_time": "Arrival Time"
        })

        st.dataframe(timings_table, use_container_width=True)
