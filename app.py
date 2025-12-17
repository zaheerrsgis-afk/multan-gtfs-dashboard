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
# LOAD GTFS FILES  (must be in the same folder as app.py)
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
col2.metric("Total Trips", len(trips))
col3.metric("Total Stops", len(stops))
col4.metric("Stop Time Records", len(stop_times))

st.markdown("---")

# ------------------------------------------------------------
# ALL STOPS MAP (like Flask version – all stops, not just one route)
# ------------------------------------------------------------
st.subheader("🗺️ All Stops (Map View)")

if len(stops) > 0:
    mean_lat = stops["stop_lat"].mean()
    mean_lon = stops["stop_lon"].mean()
    all_map = folium.Map(location=[mean_lat, mean_lon], zoom_start=12)

    for _, row in stops.iterrows():
        folium.CircleMarker(
            [row["stop_lat"], row["stop_lon"]],
            radius=3,
            color="#005be4",
            fill=True,
            fill_color="#005be4",
            popup=row["stop_name"]
        ).add_to(all_map)

    st_folium(all_map, width=900, height=450)
else:
    st.warning("No stops data found.")

st.markdown("---")

# ------------------------------------------------------------
# ROUTES LIST  (same columns idea as Flask: Name, Short, Desc)
# ------------------------------------------------------------
st.subheader("📋 Routes List")

# Keep route_id internally, but don't show it to public
clean_routes = routes[["route_id", "route_short_name", "route_long_name", "route_desc"]] \
    .rename(columns={
        "route_long_name": "Route Name",
        "route_short_name": "Short Code",
        "route_desc": "Description"
    })

st.dataframe(
    clean_routes[["Route Name", "Short Code", "Description"]],
    use_container_width=True
)

st.markdown("---")

# ------------------------------------------------------------
# SESSION STATE – to stop map from disappearing when clicking buttons
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
# ROUTE EXPLORER (like /api/route_stops and /api/route_timings in Flask)
# ------------------------------------------------------------
st.subheader("🔍 Route Explorer")

# Build human-friendly labels but keep route_id inside
route_labels = clean_routes.apply(
    lambda r: f"{r['Short Code']} – {r['Route Name']}",
    axis=1
)

selected_label = st.selectbox("Choose a Route:", route_labels)

# Get the corresponding route_id
selected_route_id = clean_routes.loc[route_labels == selected_label, "route_id"].iloc[0]
selected_route_row = clean_routes[clean_routes["route_id"] == selected_route_id].iloc[0]

st.markdown(
    f"""
    <h4 style='color:#005be4;'>Route: {selected_route_row['Short Code']}</h4>
    <p>{selected_route_row['Route Name']}</p>
    """,
    unsafe_allow_html=True
)

colA, colB = st.columns(2)
with colA:
    st.button("📍 View Stops", on_click=show_stops_action, use_container_width=True)
with colB:
    st.button("⏱ View Timings", on_click=show_times_action, use_container_width=True)

# ------------------------------------------------------------
# HELPER – Direction label (same style as Flask)
# ------------------------------------------------------------
def direction_label(x: float) -> str:
    try:
        xi = int(x)
    except (ValueError, TypeError):
        return "Unknown"
    if xi == 1:
        return "Backward [B]"
    elif xi == 0:
        return "Forward [F]"
    else:
        return "Unknown"

# ------------------------------------------------------------
# BUILD DATA FOR SELECTED ROUTE (stops + timings) USING GTFS LOGIC
# ------------------------------------------------------------

# All trips for this route, with direction_id
route_trips = trips[trips["route_id"] == selected_route_id][["trip_id", "direction_id"]]

# If no trips, nothing to show
if route_trips.empty:
    st.warning("No trips found for this route.")
else:
    # ------------------------ STOPS (like /api/route_stops) ------------------------
    # Merge stop_times with route_trips to attach direction_id
    merged = stop_times.merge(route_trips, on="trip_id", how="inner")

    # base: one row per stop_id & direction, with MIN(stop_sequence)
    base = (
        merged
        .groupby(["stop_id", "direction_id"], as_index=False)["stop_sequence"]
        .min()
        .rename(columns={"stop_sequence": "seq"})
    )

    # Join with stops to get geometry + names
    route_stops_full = base.merge(
        stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]],
        on="stop_id",
        how="left"
    )

    # Direction label and sort
    route_stops_full["Direction"] = route_stops_full["direction_id"].apply(direction_label)
    route_stops_full = route_stops_full.sort_values(["direction_id", "seq"])

    # ------------------------ TIMINGS (like /api/route_timings) ------------------------
    # Sample one representative trip per direction (smallest trip_id per direction)
    if not route_trips.empty:
        sample_trips = (
            route_trips
            .sort_values(["direction_id", "trip_id"])
            .drop_duplicates(subset=["direction_id"], keep="first")
        )

        # Merge stop_times with sample_trips
        timings = stop_times.merge(
            sample_trips[["trip_id", "direction_id"]],
            on="trip_id",
            how="inner"
        )

        timings = timings.merge(
            stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]],
            on="stop_id",
            how="left"
        )

        timings["Direction"] = timings["direction_id"].apply(direction_label)
        timings = timings.sort_values(["direction_id", "stop_sequence"])

        # Keep same “clean” columns as Flask (but NO departure_time)
        timings_table = timings[[
            "Direction",
            "stop_sequence",
            "stop_name",
            "arrival_time",
        ]].rename(columns={
            "stop_sequence": "Sequence",
            "stop_name": "Stop Name",
            "arrival_time": "Arrival Time",
        })
    else:
        timings_table = pd.DataFrame()

    # ------------------------------------------------------------
    # SHOW STOPS (MAP + TABLE) – like Flask route_stops endpoint
    # ------------------------------------------------------------
    if st.session_state.show_stops:
        st.subheader(f"📍 Stops for {selected_route_row['Route Name']}")

        if not route_stops_full.empty:
            # Map centered on route-specific stops
            map_lat = route_stops_full["stop_lat"].mean()
            map_lon = route_stops_full["stop_lon"].mean()
            route_map = folium.Map(location=[map_lat, map_lon], zoom_start=12)

            for _, srow in route_stops_full.iterrows():
                folium.CircleMarker(
                    [srow["stop_lat"], srow["stop_lon"]],
                    radius=5,
                    color="#0d6efd" if "Forward" in srow["Direction"] else "#dc3545",
                    fill=True,
                    fill_color="#0d6efd" if "Forward" in srow["Direction"] else "#dc3545",
                    popup=f"{srow['stop_name']} ({srow['Direction']})"
                ).add_to(route_map)

            st_folium(route_map, width=900, height=450)

            # Clean table with same attributes as Flask: Direction, Sequence, Stop Name, Lat, Lon
            stops_table = route_stops_full[[
                "Direction",
                "seq",
                "stop_name",
                "stop_lat",
                "stop_lon"
            ]].rename(columns={
                "seq": "Sequence",
                "stop_name": "Stop Name",
                "stop_lat": "Latitude",
                "stop_lon": "Longitude"
            })

            st.dataframe(stops_table, use_container_width=True)
        else:
            st.warning("No stops found for this route.")

    # ------------------------------------------------------------
    # SHOW TIMINGS (clean, like Flask – sample trip per direction)
    # ------------------------------------------------------------
    if st.session_state.show_times:
        st.subheader(f"⏱ Stop Timings for {selected_route_row['Route Name']}")

        if not timings_table.empty:
            st.dataframe(timings_table, use_container_width=True)
        else:
            st.warning("No timings found for this route.")
