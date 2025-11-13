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
    return routes, stops, trips, stop_times

routes, stops, trips, stop_times = load_data()

# ---------------- HEADER -------------------
st.markdown("""
<h1 style='text-align:center; color:#004AAD;'>🚌 Multan Public Transport Dashboard</h1>
<h4 style='text-align:center;'>Live GTFS Data • Powered by Punjab IT Board</h4>
<hr>
""", unsafe_allow_html=True)

# ---------------- METRIC BOXES -------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Routes", len(routes))
c2.metric("Total Trips", len(trips))
c3.metric("Total Stops", len(stops))
c4.metric("Stop Times", len(stop_times))

st.markdown("<hr>", unsafe_allow_html=True)

# ---------------- ROUTES TABLE -------------------
st.subheader("📘 Routes List")

# Table with only route_id + buttons
clean_routes = pd.DataFrame()
clean_routes["route_id"] = routes["route_id"]

# Stylish buttons (blue/green)
clean_routes["Stops"] = [
    f"<a href='?route={rid}&tab=stops' style='
        padding:6px 12px;
        background:#0066FF;
        color:white;
        border-radius:6px;
        text-decoration:none;
        font-weight:600;'>View Stops</a>"
    for rid in routes["route_id"]
]

clean_routes["Timings"] = [
    f"<a href='?route={rid}&tab=timings' style='
        padding:6px 12px;
        background:#009a44;
        color:white;
        border-radius:6px;
        text-decoration:none;
        font-weight:600;'>View Timings</a>"
    for rid in routes["route_id"]
]

# Display table
st.write(clean_routes.to_html(escape=False, index=False), unsafe_allow_html=True)

# -------------- ROUTE SELECTION (FROM URL) -----------------
query = st.experimental_get_query_params()

if "route" in query:
    selected_route = query["route"][0]
    selected_tab = query.get("tab", ["stops"])[0]

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader(f"🚌 Route: {selected_route}")

    # Filter trips of selected route
    route_trip_ids = trips[trips["route_id"] == selected_route]["trip_id"].unique()

    # Filter stops used by these trips
    used_stop_ids = stop_times[stop_times["trip_id"].isin(route_trip_ids)]["stop_id"].unique()
    route_stops = stops[stops["stop_id"].isin(used_stop_ids)]

    # ---------------- STOPS TAB -----------------
    if selected_tab == "stops":

        st.markdown("### 📍 Route Stops (Map + List)")

        # Prepare map df
        map_df = route_stops[["stop_lat", "stop_lon"]].rename(
            columns={"stop_lat": "lat", "stop_lon": "lon"}
        )

        # Show MAP (Streamlit built-in map)
        st.map(map_df)

        # Show stop list
        st.write(
            route_stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]]
        )

    # ---------------- TIMINGS TAB -----------------
    if selected_tab == "timings":

        st.markdown("### 🕒 Route Stop Timings")

        route_timings = stop_times[stop_times["trip_id"].isin(route_trip_ids)]

        # Remove arrival/departure columns
        clean_timings = route_timings[["trip_id", "stop_id", "stop_sequence"]]

        st.write(clean_timings)
