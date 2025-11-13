import streamlit as st
import pandas as pd

# ---------------- PAGE SETTINGS -------------------
st.set_page_config(
    page_title="Multan Public Transport Dashboard",
    layout="wide"
)

# ---------------- LOAD GTFS FILES -------------------
@st.cache_data
def load_data():
    routes = pd.read_csv("routes.txt")
    stops = pd.read_csv("stops.txt")
    trips = pd.read_csv("trips.txt")
    stop_times = pd.read_csv("stop_times.txt")

    # Convert lat/lon to float for map
    stops["stop_lat"] = stops["stop_lat"].astype(float)
    stops["stop_lon"] = stops["stop_lon"].astype(float)

    return routes, stops, trips, stop_times

routes, stops, trips, stop_times = load_data()

# ---------------- HEADER -------------------
st.markdown("""
<h1 style='text-align:center; color:#004AAD;'>🚌 Multan Public Transport Dashboard</h1>
<h4 style='text-align:center;'>Live GTFS Data • Powered by Punjab IT Board</h4>
<hr>
""", unsafe_allow_html=True)

# ---------------- METRICS -------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Routes", len(routes))
c2.metric("Total Trips", len(trips))
c3.metric("Total Stops", len(stops))
c4.metric("Stop Times", len(stop_times))

st.markdown("<hr>", unsafe_allow_html=True)

# ---------------- ROUTES LIST (CLEAN) -------------------
st.subheader("📘 Routes List")

clean_routes = pd.DataFrame()
clean_routes["Route ID"] = routes["route_id"]

clean_routes["Stops"] = [
    f"""
    <a href='/?route={rid}&tab=stops' 
       style='background:#007bff; padding:6px 12px; color:white; 
       border-radius:6px; text-decoration:none; font-weight:600;'>
       View Stops
    </a>
    """
    for rid in routes["route_id"]
]

clean_routes["Timings"] = [
    f"""
    <a href='/?route={rid}&tab=timings' 
       style='background:#28a745; padding:6px 12px; color:white; 
       border-radius:6px; text-decoration:none; font-weight:600;'>
       View Timings
    </a>
    """
    for rid in routes["route_id"]
]

st.write(clean_routes.to_html(escape=False, index=False), unsafe_allow_html=True)

# ---------------- URL PARAM HANDLING -------------------
query = st.experimental_get_query_params()

if "route" in query:
    selected_route = query["route"][0]
    selected_tab = query.get("tab", ["stops"])[0]

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader(f"🚌 Route: {selected_route}")

    # Get trip IDs for this route
    r_trips = trips[trips["route_id"] == selected_route]["trip_id"].unique()

    # Get stop IDs
    stop_ids = stop_times[stop_times["trip_id"].isin(r_trips)]["stop_id"].unique()
    route_stops = stops[stops["stop_id"].isin(stop_ids]]

    # ---------------- SHOW STOPS -------------------
    if selected_tab == "stops":
        st.markdown("## 📍 Route Stops (Map + List)")

        if len(route_stops) == 0:
            st.warning("No stops found for this route.")
        else:
            # Prepare map dataframe
            map_df = pd.DataFrame({
                "lat": route_stops["stop_lat"],
                "lon": route_stops["stop_lon"]
            })

            # Show map
            st.map(map_df)

            # Show table
            st.dataframe(
                route_stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]],
                use_container_width=True
            )

    # ---------------- SHOW TIMINGS -------------------
    if selected_tab == "timings":
        st.markdown("## 🕒 Stop Timings")

        r_times = stop_times[stop_times["trip_id"].isin(r_trips)]

        clean_times = r_times[["trip_id", "stop_id", "stop_sequence"]]

        st.dataframe(clean_times, use_container_width=True)
