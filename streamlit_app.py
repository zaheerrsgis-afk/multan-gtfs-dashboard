import streamlit as st
import pandas as pd

st.set_page_config(page_title="Multan GTFS Dashboard", layout="wide")

st.title("🚌 Multan Public Transport Dashboard")
st.caption("Live GTFS Data • No Database Required • Powered by Punjab IT Board")

# ---------------------------
# Load GTFS CSV Files
# ---------------------------
@st.cache_data
def load_gtfs():
    routes = pd.read_csv("routes.txt")
    trips = pd.read_csv("trips.txt")
    stops = pd.read_csv("stops.txt")
    stop_times = pd.read_csv("stop_times.txt")
    return routes, trips, stops, stop_times

routes, trips, stops, stop_times = load_gtfs()

# ---------------------------
# Summary
# ---------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Routes", len(routes))
c2.metric("Total Trips", len(trips))
c3.metric("Total Stops", len(stops))
c4.metric("Stop Times Records", len(stop_times))

st.divider()

# ---------------------------
# Show Tables
# ---------------------------
st.subheader("Routes")
st.dataframe(routes, use_container_width=True)

st.subheader("Trips")
st.dataframe(trips, use_container_width=True)

st.subheader("Stops")
st.dataframe(stops, use_container_width=True)

st.subheader("Stop Times")
st.dataframe(stop_times, use_container_width=True)
