import streamlit as st
import psycopg2
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# ----------------------------------------------------------
# DATABASE CONNECTION
# ----------------------------------------------------------
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DBNAME"
# Replace with your correct connection string

def get_conn():
    return psycopg2.connect(DATABASE_URL)


# ----------------------------------------------------------
# LOAD DATA HELPERS
# ----------------------------------------------------------
@st.cache_data(ttl=300)
def get_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM routes")
    routes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM stops")
    stops = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trips")
    trips = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM stop_times")
    times = cur.fetchone()[0]

    cur.close(); conn.close()
    return routes, stops, trips, times


@st.cache_data(ttl=300)
def load_all_stops():
    conn = get_conn()
    df = pd.read_sql("SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops", conn)
    conn.close()
    return df


@st.cache_data(ttl=300)
def load_routes():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT route_id, route_long_name, route_short_name, route_desc
        FROM routes ORDER BY route_long_name
    """, conn)
    conn.close()
    return df


def load_route_stops(route_id):
    conn = get_conn()
    df = pd.read_sql(f"""
        SELECT DISTINCT 
            s.stop_id,
            s.stop_name,
            s.stop_lat,
            s.stop_lon
        FROM stop_times st
        JOIN stops s ON s.stop_id = st.stop_id
        JOIN trips t ON t.trip_id = st.trip_id
        WHERE t.route_id = '{route_id}'
        ORDER BY s.stop_name
    """, conn)
    conn.close()
    return df


def load_route_timing(route_id):
    conn = get_conn()
    df = pd.read_sql(f"""
        SELECT 
            s.stop_name,
            st.arrival_time,
            st.departure_time,
            st.stop_sequence,
            CASE t.direction_id 
                WHEN 0 THEN 'Forward [F]'
                WHEN 1 THEN 'Backward [B]'
                ELSE 'Unknown'
            END AS direction
        FROM stop_times st
        JOIN stops s ON s.stop_id = st.stop_id
        JOIN trips t ON t.trip_id = st.trip_id
        WHERE t.route_id = '{route_id}'
        ORDER BY direction, st.stop_sequence
    """, conn)
    conn.close()
    return df


# ----------------------------------------------------------
# UI STARTS HERE
# ----------------------------------------------------------
st.set_page_config(page_title="Multan GTFS Dashboard", layout="wide")

st.title("🚍 Multan Public Transport Dashboard")
st.caption("Live GTFS Data • Powered by Punjab IT Board")

# Summary Cards
routes, stops, trips, times = get_summary()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Routes", routes)
c2.metric("Stops", stops)
c3.metric("Trips", trips)
c4.metric("Stop Timings", times)

st.markdown("---")

# ----------------------------------------------------------
# MAP OF ALL STOPS
# ----------------------------------------------------------
st.subheader("🗺️ All Stops on Map")

df_stops = load_all_stops()

m = folium.Map(location=[30.20, 71.50], zoom_start=12)
cluster = MarkerCluster().add_to(m)

for _, row in df_stops.iterrows():
    folium.CircleMarker(
        location=[row.stop_lat, row.stop_lon],
        radius=3,
        color="blue",
        fill=True,
        popup=row.stop_name
    ).add_to(cluster)

st_folium(m, height=450)

st.markdown("---")

# ----------------------------------------------------------
# ROUTE LIST
# ----------------------------------------------------------
st.subheader("📋 Routes List")

routes_df = load_routes()
st.dataframe(routes_df, use_container_width=True)

st.markdown("### 🔍 View Details for a Route")

route_id = st.selectbox("Select Route", routes_df['route_id'])

if route_id:

    rname = routes_df.loc[routes_df.route_id == route_id, "route_long_name"].iloc[0]

    st.markdown(f"## 🚏 Stops for **{rname}**")
    df_route_stops = load_route_stops(route_id)
    st.dataframe(df_route_stops, use_container_width=True)

    st.markdown("---")

    st.markdown(f"## ⏱ Stop Timings for **{rname}**")
    df_timing = load_route_timing(route_id)

    # Group by direction
    dirs = df_timing["direction"].unique()

    for d in dirs:
        st.markdown(f"### {d}")
        sub = df_timing[df_timing.direction == d]
        st.dataframe(sub, use_container_width=True)

