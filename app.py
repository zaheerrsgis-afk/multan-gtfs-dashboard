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
# LOAD GTFS FILES (FROM REPO ROOT)
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
# TOP METRICS
# ------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Routes", len(routes))
col2.metric("Total Stops", len(stops))
col3.metric("Total Trips", len(trips))
col4.metric("Stop Timings", len(stop_times))

st.markdown("---")

# ------------------------------------------------------------
# ALL STOPS MAP (GLOBAL VIEW)
# ------------------------------------------------------------
st.subheader("🗺️ All Stops (Map View)")

if not stops.empty:
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
            popup=f"{s['stop_name']}",
        ).add_to(m_all)

    st_folium(m_all, width=900, height=450)
else:
    st.warning("No stops found in GTFS data.")

st.markdown("---")

# ------------------------------------------------------------
# GTFS DATA OVERVIEW (LIKE OLD FLASK /dashboard)
# ------------------------------------------------------------
st.subheader("📊 GTFS Data Overview (Sample Like API Dashboard)")

tab1, tab2, tab3, tab4 = st.tabs(["Routes", "Stops", "Trips", "Stop Times"])

# ROUTES: route_id, route_short_name, route_long_name  (LIMIT 20)
with tab1:
    st.markdown("**Routes (sample)**")
    cols = ["route_id", "route_short_name", "route_long_name"]
    available = [c for c in cols if c in routes.columns]
    routes_preview = routes[available].head(20)
    st.dataframe(routes_preview, use_container_width=True)

# STOPS: stop_id, stop_name, stop_lat, stop_lon  (LIMIT 20)
with tab2:
    st.markdown("**Stops (sample)**")
    cols = ["stop_id", "stop_name", "stop_lat", "stop_lon"]
    available = [c for c in cols if c in stops.columns]
    stops_preview = stops[available].head(20)
    st.dataframe(stops_preview, use_container_width=True)

# TRIPS: trip_id, route_id, service_id, trip_headsign  (LIMIT 20)
with tab3:
    st.markdown("**Trips (sample)**")
    cols = ["trip_id", "route_id", "service_id", "trip_headsign"]
    available = [c for c in cols if c in trips.columns]
    trips_preview = trips[available].head(20)
    st.dataframe(trips_preview, use_container_width=True)

# STOP TIMES: trip_id, arrival_time, departure_time, stop_id  (LIMIT 20)
with tab4:
    st.markdown("**Stop Times (sample)**")
    cols = ["trip_id", "arrival_time", "departure_time", "stop_id"]
    available = [c for c in cols if c in stop_times.columns]
    stop_times_preview = stop_times[available].head(20)
    st.dataframe(stop_times_preview, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------
# SESSION STATE FOR DETAIL TOGGLES
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
# ADVANCED ROUTE EXPLORER (HIDDEN BY DEFAULT)
# ------------------------------------------------------------
with st.expander("🔍 Detailed Route Explorer (Forward / Backward) – internal / optional"):
    st.write("Select a route to view its forward/backward stops and detailed timings.")

    # internal clean routes (for dropdown)
    clean_routes = routes[["route_id", "route_short_name", "route_long_name"]].copy()

    route_options = []
    for _, r in clean_routes.iterrows():
        label = f"{r['route_short_name']} – {r['route_long_name']}"
        route_options.append((label, r["route_id"]))

    labels = [x[0] for x in route_options]
    selected_label = st.selectbox("Choose a Route:", labels)
    selected_route = dict(route_options)[selected_label]

    # Selected route row
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

    # ------------ BUILD ROUTE DATA WITH DIRECTION -------------
    route_trips = trips[trips["route_id"] == selected_route][["trip_id", "direction_id"]]
    route_stop_times = stop_times[stop_times["trip_id"].isin(route_trips["trip_id"])]
    route_stop_times = route_stop_times.merge(route_trips, on="trip_id", how="left")
    route_full = route_stop_times.merge(stops, on="stop_id", how="left")

    def dir_label(x):
        if x == 0:
            return "Forward"
        elif x == 1:
            return "Backward"
        else:
            return "Unknown"

    route_full["direction"] = route_full["direction_id"].apply(dir_label)

    # ------------ SHOW ROUTE STOPS (MAP + TABLE) --------------
    if st.session_state.show_stops:
        st.subheader("🗺️ Route Stops (Forward / Backward)")

        route_stops = route_full[
            ["stop_id", "stop_name", "stop_lat", "stop_lon", "direction"]
        ].drop_duplicates()

        if len(route_stops) > 0:
            m = folium.Map(
                location=[route_stops["stop_lat"].mean(), route_stops["stop_lon"].mean()],
                zoom_start=12,
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
                    popup=f"{stop['stop_name']} ({stop['direction']})",
                ).add_to(m)

            st_folium(m, width=900, height=500)

            stops_table = route_stops[["stop_name", "stop_lat", "stop_lon", "direction"]].copy()
            stops_table = stops_table.rename(
                columns={
                    "stop_name": "Stop",
                    "stop_lat": "Latitude",
                    "stop_lon": "Longitude",
                    "direction": "Direction",
                }
            )
            st.dataframe(stops_table, use_container_width=True)
        else:
            st.warning("No stops found for this route.")

    # ------------ SHOW STOP TIMINGS (ARRIVAL ONLY) ------------
    if st.session_state.show_times:
        st.subheader("⏱ Stop Timings (Forward / Backward) – Arrival Only")

        if len(route_full) == 0:
            st.warning("No timings found for this route.")
        else:
            timings_table = route_full[["direction", "trip_id", "stop_name", "arrival_time"]].copy()
            timings_table = timings_table.sort_values(
                ["direction", "trip_id", "arrival_time"]
            )
            timings_table = timings_table.rename(
                columns={
                    "direction": "Direction",
                    "trip_id": "Trip",
                    "stop_name": "Stop",
                    "arrival_time": "Arrival Time",
                }
            )
            st.dataframe(timings_table, use_container_width=True)
