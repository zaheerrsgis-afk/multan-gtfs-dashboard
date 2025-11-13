# ================================================================
# 🚍 MULTAN PUBLIC TRANSPORT GTFS DASHBOARD – FINAL PROFESSIONAL VERSION
# ================================================================
# ✅ Bootstrap 5 Interface
# ✅ Leaflet Map (All Stops)
# ✅ Routes with "View Stops" and "View Timings"
# ✅ Clean stop timings (no duplicates)
# ✅ Forward / Backward direction labels
# ✅ Live PostgreSQL connection
# ================================================================

from flask import Flask, jsonify, render_template_string
import psycopg2, sys

app = Flask(__name__)

# ---------- PostgreSQL Connection ----------
DB = dict(
    host="localhost",
    database="Multan_GTFS",
    user="postgres",
    password="Koldodu@123",
    port=5432
)

def connect():
    return psycopg2.connect(**DB)


# ==========================================================
# HOME DASHBOARD
# ==========================================================
@app.route("/")
def dashboard():
    try:
        conn = connect()
        cur = conn.cursor()

        # Summary Counts
        cur.execute("SELECT COUNT(*) FROM routes;")
        total_routes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM stops;")
        total_stops = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM trips;")
        total_trips = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM stop_times;")
        total_times = cur.fetchone()[0]

        # Routes
        cur.execute("""
            SELECT route_id, route_long_name, route_short_name, COALESCE(route_desc,'')
            FROM routes ORDER BY route_long_name;
        """)
        routes = cur.fetchall()

        # All Stops (Map)
        cur.execute("""
            SELECT stop_name, stop_lat, stop_lon
            FROM stops
            WHERE stop_lat IS NOT NULL AND stop_lon IS NOT NULL;
        """)
        stops = cur.fetchall()

        cur.close(); conn.close()
    except Exception as e:
        print("❌ Database error:", e, file=sys.stderr)
        routes, stops = [], []
        total_routes = total_stops = total_trips = total_times = 0

    # ----------------- HTML -----------------
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Multan Public Transport Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

        <style>
            body { background:#f8f9fa; font-family:'Segoe UI', Arial; }
            h1 { color:#0056b3; text-align:center; margin-bottom:15px; }
            #map { height: 480px; border-radius:10px; margin-bottom:30px; }
            .stat-card { background:white; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1);
                         padding:20px; text-align:center; }
            .section-title { color:#007bff; margin-top:40px; }
            table { background:white; border-radius:8px; overflow:hidden; }
            footer { text-align:center; margin-top:40px; color:#777; font-size:13px; }
            .btn-view { font-size:13px; padding:3px 8px; margin-right:4px; }
        </style>
    </head>

    <body>
        <div class="container my-4">
            <h1>🚍 Multan Public Transport Dashboard</h1>
            <p class="text-center text-muted mb-4">Live GTFS Data • Powered by Punjab IT Board</p>

            <!-- STATS -->
            <div class="row text-center mb-4">
                <div class="col-md-3"><div class="stat-card"><h3>{{total_routes}}</h3><p>Routes</p></div></div>
                <div class="col-md-3"><div class="stat-card"><h3>{{total_stops}}</h3><p>Stops</p></div></div>
                <div class="col-md-3"><div class="stat-card"><h3>{{total_trips}}</h3><p>Trips</p></div></div>
                <div class="col-md-3"><div class="stat-card"><h3>{{total_times}}</h3><p>Stop Timings</p></div></div>
            </div>

            <!-- MAP -->
            <h4 class="section-title">🗺️ All Stops (Map View)</h4>
            <div id="map"></div>

            <!-- ROUTES TABLE -->
            <h4 class="section-title">📋 Routes List</h4>
            <table class="table table-striped table-bordered align-middle">
                <thead class="table-primary">
                    <tr><th>Route Name</th><th>Short Code</th><th>Description</th><th>Actions</th></tr>
                </thead>
                <tbody>
                {% for r in routes %}
                    <tr>
                        <td>{{r[1]}}</td>
                        <td>{{r[2]}}</td>
                        <td>{{r[3]}}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary btn-view"
                                    onclick="viewStops('{{r[0]}}','{{r[1]}}')">View Stops</button>
                            <button class="btn btn-sm btn-outline-success btn-view"
                                    onclick="viewTimings('{{r[0]}}','{{r[1]}}')">View Timings</button>
                        </td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>

            <div id="routeData" class="mt-4"></div>

            <footer>© 2025 Punjab IT Board • Multan GTFS Portal</footer>
        </div>

        <script>
            // Initialize map
            const map = L.map('map').setView([30.2, 71.5], 12);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18, attribution: '© OpenStreetMap'
            }).addTo(map);

            // All Stops
            const stops = {{ stops|tojson }};
            stops.forEach(s => {
                if (s[1] && s[2])
                    L.circleMarker([s[1], s[2]], {radius:4, color:'#007bff'})
                        .bindPopup('<b>' + s[0] + '</b>').addTo(map);
            });

            // View Stops
            function viewStops(route_id, route_name){
                $("#routeData").html("<p class='text-muted'>Loading stops for <b>" + route_name + "</b>...</p>");
                fetch('/api/route_stops/' + encodeURIComponent(route_id))
                    .then(res => res.json())
                    .then(data => {
                        if (data.error) return $("#routeData").html("<div class='alert alert-danger'>" + data.error + "</div>");
                        if (data.length === 0) return $("#routeData").html("<div class='alert alert-warning'>No stops found.</div>");
                        let html = "<h5 class='mt-3'>🚏 Stops for <b>" + route_name + "</b></h5>";
                        html += "<table class='table table-bordered table-sm'><thead class='table-light'><tr><th>#</th><th>Stop Name</th><th>Direction</th><th>Latitude</th><th>Longitude</th></tr></thead><tbody>";
                        data.forEach((s, i) => {
                            html += `<tr><td>${i+1}</td><td>${s.stop_name}</td><td>${s.direction}</td><td>${s.latitude}</td><td>${s.longitude}</td></tr>`;
                        });
                        html += "</tbody></table>";
                        $("#routeData").html(html);
                    })
                    .catch(err => $("#routeData").html("<div class='alert alert-danger'>Failed to load stops ("+err.message+").</div>"));
            }

            // View Timings
            function viewTimings(route_id, route_name){
                $("#routeData").html("<p class='text-muted'>Loading timings for <b>" + route_name + "</b>...</p>");
                fetch('/api/route_timings/' + encodeURIComponent(route_id))
                    .then(res => res.json())
                    .then(data => {
                        if (data.error) return $("#routeData").html("<div class='alert alert-danger'>" + data.error + "</div>");
                        if (data.length === 0) return $("#routeData").html("<div class='alert alert-warning'>No timings found.</div>");
                        let html = "<h5 class='mt-3'>⏱ Stop Timings for <b>" + route_name + "</b></h5>";
                        html += "<table class='table table-bordered table-sm'><thead class='table-light'><tr><th>#</th><th>Stop Name</th><th>Arrival</th><th>Departure</th><th>Direction</th></tr></thead><tbody>";
                        data.forEach((s, i) => {
                            html += `<tr><td>${i+1}</td><td>${s.stop_name}</td><td>${s.arrival_time}</td><td>${s.departure_time}</td><td>${s.direction}</td></tr>`;
                        });
                        html += "</tbody></table>";
                        $("#routeData").html(html);
                    })
                    .catch(err => $("#routeData").html("<div class='alert alert-danger'>Failed to load timings ("+err.message+").</div>"));
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html,
        total_routes=total_routes,
        total_stops=total_stops,
        total_trips=total_trips,
        total_times=total_times,
        routes=routes,
        stops=stops
    )


# ==========================================================
# API: Route Stops
# ==========================================================
@app.route("/api/route_stops/<route_id>")
def route_stops(route_id):
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("""
            WITH base AS (
                SELECT st.stop_id, MIN(st.stop_sequence) AS seq, t.direction_id
                FROM stop_times st
                JOIN trips t ON t.trip_id = st.trip_id
                WHERE t.route_id = %s
                GROUP BY st.stop_id, t.direction_id
            )
            SELECT s.stop_name, s.stop_lat, s.stop_lon,
                   CASE WHEN b.direction_id=1 THEN 'Backward [B]' ELSE 'Forward [F]' END AS direction,
                   b.seq
            FROM base b
            JOIN stops s ON s.stop_id=b.stop_id
            ORDER BY b.direction_id, b.seq;
        """, (route_id,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify([{
            "stop_name": r[0],
            "latitude": float(r[1]),
            "longitude": float(r[2]),
            "direction": r[3]
        } for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================================
# API: Route Timings (Clean, no duplicates)
# ==========================================================
@app.route("/api/route_timings/<route_id>")
def route_timings(route_id):
    try:
        conn = connect()
        cur = conn.cursor()

        # Select one sample trip per direction to remove duplicates
        cur.execute("""
            WITH sample_trips AS (
                SELECT MIN(trip_id) AS trip_id, direction_id
                FROM trips
                WHERE route_id = %s
                GROUP BY direction_id
            )
            SELECT s.stop_name,
                   st.arrival_time,
                   st.departure_time,
                   CASE WHEN t.direction_id=1 THEN 'Backward [B]' ELSE 'Forward [F]' END AS direction,
                   st.stop_sequence
            FROM stop_times st
            JOIN trips t ON t.trip_id = st.trip_id
            JOIN sample_trips samp ON samp.trip_id = t.trip_id
            JOIN stops s ON s.stop_id = st.stop_id
            ORDER BY t.direction_id, st.stop_sequence;
        """, (route_id,))

        rows = cur.fetchall()
        cur.close(); conn.close()

        return jsonify([
            {
                "stop_name": r[0],
                "arrival_time": r[1],
                "departure_time": r[2],
                "direction": r[3],
                "sequence": r[4]
            }
            for r in rows
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================================
# MAIN ENTRY
# ==========================================================
if __name__ == "__main__":
    print("✅ Multan GTFS Dashboard running at http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
