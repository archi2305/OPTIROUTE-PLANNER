import time
from difflib import get_close_matches
from typing import Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components
import geonamescache
from geopy.distance import geodesic
from geopy.exc import GeopyError
from geopy.geocoders import Nominatim

from algorithms.dijkstra import dijkstra, get_path
from algorithms.graph import Graph
from algorithms.visualizer import draw_graph

# Basic Streamlit page setup.
st.set_page_config(
    page_title="OptiRoute Planner",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Global UI styling for dashboard look and layout behavior.
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700&display=swap" rel="stylesheet" />
<style>
  .block-container { padding-top: 0.5rem; padding-bottom: 0.75rem; max-width: min(100%, 1920px); }
  div[data-testid="stAppViewContainer"] .main { overflow-x: hidden; }
  [data-testid="column"] { min-width: 0 !important; }
  [data-testid="stVerticalBlock"] > div { min-width: 0; }
  iframe[title="streamlit_embed"] { width: 100% !important; max-width: 100%; }
  h1, h2, h3, p, label { font-family: "Plus Jakarta Sans", system-ui, sans-serif !important; }
  .or-header-wrap { padding: 0.5rem 0 0.1rem; margin: 0 0 0.2rem; }
  .or-header-title {
    font-size: 1.85rem; font-weight: 700; letter-spacing: -0.03em; color: #0f172a !important;
    margin: 0; line-height: 1.2;
  }
  .or-header-sub { color: #64748b; font-size: 0.95rem; margin: 0.5rem 0 0.85rem; line-height: 1.45; }
  .or-header-hr { border: none; border-top: 1px solid #e2e8f0; margin: 0.25rem 0 0.6rem; }
  .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin: 0.15rem 0 0.45rem; }
  @media (max-width: 1100px) { .kpi-row { grid-template-columns: repeat(2, 1fr); } }
  .kpi-card {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 0.55rem 0.75rem;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
  }
  .kpi-emoji { font-size: 1.05rem; line-height: 1; }
  .kpi-t { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin: 0.25rem 0 0.1rem; }
  .kpi-v { font-size: 1.15rem; font-weight: 700; color: #0f172a; }
  .map-legend { font-size: 0.8rem; color: #334155; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.45rem 0.7rem; margin: 0 0 0.4rem; }
  .rc-best { border-left: 4px solid #22c55e; background: #f0fdf4; border-radius: 10px; padding: 0.9rem 1rem; border: 1px solid #bbf7d0; margin: 0.5rem 0; }
  .rc-alt { border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.9rem 1rem; background: #fff; margin: 0.5rem 0; }
  .rc-t { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; }
  .rc-path { color: #0f172a; font-size: 0.92rem; line-height: 1.4; font-weight: 500; }
  .sec-t { font-size: 1.05rem; font-weight: 600; color: #0f172a; }
</style>
""",
    unsafe_allow_html=True,
)

# Session defaults so reruns keep route/map/simulation state.
if "routes_result" not in st.session_state:
    st.session_state.routes_result = None
if "route_edges_list" not in st.session_state:
    st.session_state.route_edges_list = None
if "pending_sim" not in st.session_state:
    st.session_state.pending_sim = False
if "replay_sim" not in st.session_state:
    st.session_state.replay_sim = False

st.markdown(
    """
<div class="or-header-wrap">
  <h1 class="or-header-title">🚚 OptiRoute Command Center</h1>
  <p class="or-header-sub">Real-time logistics routing • Multi-truck simulation • Smart optimization</p>
  <hr class="or-header-hr" />
</div>
    """,
    unsafe_allow_html=True,
)


MAP_IFRAME_HEIGHT = 560
INDIA_BOUNDS = {"min_lat": 6.0, "max_lat": 38.5, "min_lon": 68.0, "max_lon": 97.5}
NEARBY_CONNECTION_THRESHOLD_KM = 300.0
BASE_CITY_COORDS = {
    "Delhi": (28.6139, 77.2090),
    "Noida": (28.5355, 77.3910),
    "Ghaziabad": (28.6692, 77.4538),
    "Meerut": (28.9845, 77.7064),
    "Gurgaon": (28.4595, 77.0266),
    "Faridabad": (28.4089, 77.3178),
}


def _normalize_city_name(name: str) -> str:
    return " ".join(part for part in name.strip().split())


def _parse_lat_lon_input(value: str) -> Optional[Tuple[float, float]]:
    txt = value.strip()
    if "," not in txt:
        return None
    parts = [p.strip() for p in txt.split(",")]
    if len(parts) != 2:
        return None
    try:
        lat = float(parts[0])
        lon = float(parts[1])
    except ValueError:
        return None
    if not (
        INDIA_BOUNDS["min_lat"] <= lat <= INDIA_BOUNDS["max_lat"]
        and INDIA_BOUNDS["min_lon"] <= lon <= INDIA_BOUNDS["max_lon"]
    ):
        return None
    return (lat, lon)


def _looks_like_partial_coordinate(value: str) -> bool:
    txt = value.strip().lower()
    if not txt:
        return False
    if "," in txt:
        return False
    if txt in {"lat", "lon", "latitude", "longitude"}:
        return True
    allowed = set("0123456789.-+ ")
    return all(ch in allowed for ch in txt)


@st.cache_data(show_spinner=False)
def build_india_location_index() -> tuple[dict[str, tuple[float, float]], list[str]]:
    gc = geonamescache.GeonamesCache()
    cities = gc.get_cities()
    names_to_coords: dict[str, tuple[float, float]] = {}
    for city in cities.values():
        if city.get("countrycode") != "IN":
            continue
        try:
            lat = float(city["latitude"])
            lon = float(city["longitude"])
        except (TypeError, ValueError, KeyError):
            continue
        if not (
            INDIA_BOUNDS["min_lat"] <= lat <= INDIA_BOUNDS["max_lat"]
            and INDIA_BOUNDS["min_lon"] <= lon <= INDIA_BOUNDS["max_lon"]
        ):
            continue
        canonical = _normalize_city_name(str(city.get("name", ""))).lower()
        if canonical and canonical not in names_to_coords:
            names_to_coords[canonical] = (lat, lon)
        for alt in city.get("alternatenames", []):
            alias = _normalize_city_name(str(alt)).lower()
            if alias and alias not in names_to_coords:
                names_to_coords[alias] = (lat, lon)
    for base_name, base_coords in BASE_CITY_COORDS.items():
        names_to_coords.setdefault(base_name.lower(), base_coords)
    return names_to_coords, list(names_to_coords.keys())


def geocode_from_offline_india_index(location: str) -> Optional[Tuple[float, float]]:
    query = _normalize_city_name(location).lower()
    if not query:
        return None
    names_to_coords, keys = build_india_location_index()
    exact = names_to_coords.get(query)
    if exact is not None:
        return exact
    near = get_close_matches(query, keys, n=1, cutoff=0.86)
    if near:
        return names_to_coords.get(near[0])
    return None


@st.cache_resource(show_spinner=False)
def get_geolocator() -> Nominatim:
    return Nominatim(user_agent="optiroute_planner_app")


@st.cache_data(show_spinner=False)
def geocode_india_location(location: str) -> Optional[Tuple[float, float]]:
    geolocator = get_geolocator()
    loc = geolocator.geocode(f"{location}, India", exactly_one=True, timeout=10)
    if loc is None:
        return None
    if not (
        INDIA_BOUNDS["min_lat"] <= loc.latitude <= INDIA_BOUNDS["max_lat"]
        and INDIA_BOUNDS["min_lon"] <= loc.longitude <= INDIA_BOUNDS["max_lon"]
    ):
        return None
    return (loc.latitude, loc.longitude)


def safe_geocode_india_location(location: str) -> tuple[Optional[Tuple[float, float]], Optional[str]]:
    lat_lon = _parse_lat_lon_input(location)
    if lat_lon is not None:
        return lat_lon, None
    if _looks_like_partial_coordinate(location):
        return None, "Enter full coordinates as 'lat,lon' (example: 23.3441,86.3397)."
    offline_coords = geocode_from_offline_india_index(location)
    if offline_coords is not None:
        return offline_coords, None
    try:
        return geocode_india_location(location), None
    except GeopyError:
        return (
            None,
            "Geocoding service is currently unavailable. "
            "Try again later or enter coordinates as 'lat,lon' within India.",
        )
    except Exception:
        return (
            None,
            "Unable to validate location due to a network/proxy issue. "
            "You can still enter coordinates as 'lat,lon' within India.",
        )


def build_node_positions(coords_map: dict[str, tuple[float, float]]) -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    avg_lat = sum(lat for lat, _ in coords_map.values()) / len(coords_map)
    avg_lon = sum(lon for _, lon in coords_map.values()) / len(coords_map)
    for city, (lat, lon) in coords_map.items():
        out[city] = ((lon - avg_lon) * 2200, -(lat - avg_lat) * 2200)
    return out


def extend_graph_with_location(
    g: Graph,
    coords_map: dict[str, tuple[float, float]],
    location_name: str,
    location_coords: tuple[float, float],
    traffic: float,
    threshold_km: float = NEARBY_CONNECTION_THRESHOLD_KM,
) -> tuple[bool, bool]:
    if location_name not in g.graph:
        g.add_location(location_name)
    coords_map[location_name] = location_coords
    connected = False
    nearest_city = None
    nearest_distance = float("inf")
    for city, city_coords in coords_map.items():
        if city == location_name:
            continue
        dist_km = geodesic(location_coords, city_coords).km
        if dist_km < nearest_distance:
            nearest_distance = dist_km
            nearest_city = city
        if dist_km <= threshold_km:
            g.add_road(location_name, city, max(1, int(round(dist_km * traffic))))
            connected = True
    if connected:
        return True, False
    if nearest_city is None:
        return False, False
    g.add_road(location_name, nearest_city, max(1, int(round(nearest_distance * traffic))))
    return True, True

# Build a weighted city graph; traffic scales all road costs.
def build_graph(traffic: float) -> Graph:
    g = Graph()
    roads = [
        ("Delhi", "Noida", 20),
        ("Delhi", "Gurgaon", 15),
        ("Noida", "Ghaziabad", 10),
        ("Ghaziabad", "Meerut", 40),
        ("Gurgaon", "Faridabad", 25),
        ("Faridabad", "Noida", 30),
        ("Meerut", "Delhi", 70),
    ]
    for c1, c2, d in roads:
        g.add_road(c1, c2, int(d * traffic))
    return g


# Clone graph safely so route experiments do not mutate the original.
def clone_graph(g: Graph) -> Graph:
    h = Graph()
    seen = set()
    for a in g.graph:
        for b, w in g.graph[a]:
            t = (a, b) if a <= b else (b, a)
            if t in seen:
                continue
            seen.add(t)
            h.add_road(t[0], t[1], w)
    return h


# Remove one undirected edge from both adjacency lists.
def remove_undirected_edge(g: Graph, u: str, v: str) -> None:
    g.graph[u] = [(n, w) for n, w in g.graph[u] if n != v]
    g.graph[v] = [(n, w) for n, w in g.graph[v] if n != u]


# Temporarily penalize an edge to force alternate route discovery.
def _multiply_edge_weight_in_place(g: Graph, u: str, v: str, factor: float) -> None:
    def scale(w):
        return int(round(w * factor))

    g.graph[u] = [(n, scale(w) if n == v else w) for n, w in g.graph[u]]
    g.graph[v] = [(n, scale(w) if n == u else w) for n, w in g.graph[v]]


# Hashable route form for quick path equality checks.
def path_key(path: list) -> tuple:
    return tuple(path)


def find_next_distinct_route(
    g_base: Graph,
    source: str,
    dest: str,
    avoid_paths: list,
) -> Optional[Tuple[list, float]]:
    """A route different from every path in avoid_paths; original graph is never modified."""
    best: tuple[list, float] | None = None
    best_d = float("inf")
    # Pass 1: try removing one edge from known routes.
    for ref in avoid_paths:
        for i in range(len(ref) - 1):
            u, v = ref[i], ref[i + 1]
            g2 = clone_graph(g_base)
            remove_undirected_edge(g2, u, v)
            d2, pr2 = dijkstra(g2, source)
            if d2[dest] == float("inf"):
                continue
            p2 = get_path(pr2, source, dest)
            if not p2 or p2[0] != source:
                continue
            if any(path_key(p2) == path_key(a) for a in avoid_paths):
                continue
            if d2[dest] < best_d:
                best_d = d2[dest]
                best = (p2, d2[dest])
    if best is not None:
        return best
    # Pass 2: if removal fails, heavily penalize shared edges.
    for ref in avoid_paths:
        for i in range(len(ref) - 1):
            u, v = ref[i], ref[i + 1]
            g2 = clone_graph(g_base)
            _multiply_edge_weight_in_place(g2, u, v, 40.0)
            d2, pr2 = dijkstra(g2, source)
            if d2[dest] == float("inf"):
                continue
            p2 = get_path(pr2, source, dest)
            if not p2 or p2[0] != source:
                continue
            if any(path_key(p2) == path_key(a) for a in avoid_paths):
                continue
            if d2[dest] < best_d:
                best_d = d2[dest]
                best = (p2, d2[dest])
    return best


# Primary route first, then add distinct alternatives for extra trucks.
def compute_fleet_routes(g: Graph, source: str, dest: str, n_trucks: int) -> list:
    dist, prev = dijkstra(g, source)
    if dist[dest] == float("inf"):
        return []
    p0 = get_path(prev, source, dest)
    if not p0 or p0[0] != source:
        return []
    d0 = dist[dest]
    out = [(p0, d0)]
    if n_trucks < 2:
        return out
    avoid: list = [p0]
    for _ in range(1, n_trucks):
        nxt = find_next_distinct_route(g, source, dest, avoid)
        if nxt is None:
            break
        p_new, d_new = nxt
        out.append((p_new, d_new))
        avoid.append(p_new)
    return out


# Convert node path into edge pairs for map highlighting.
def path_to_edges(path: list) -> list:
    if len(path) < 2:
        return []
    return [(path[i], path[i + 1]) for i in range(len(path) - 1)]


# KPI payload shown in the top cards.
def kpi_value(routes, fleet_size_session: int, speed_kmh: float = 40.0):
    if routes and len(routes) > 0:
        p0, d0 = routes[0]
        est_h = d0 / speed_kmh if d0 is not None else 0.0
        return {
            "trucks": len(routes),
            "stops": len(p0),
            "dist": d0,
            "time_h": est_h,
        }
    return {
        "trucks": fleet_size_session,
        "stops": 0,
        "dist": None,
        "time_h": None,
    }


# Compute top-card values from current session state.
rts0 = st.session_state.routes_result
f_sz = int(st.session_state.get("fleet_sz", 2))
k0 = kpi_value(rts0, f_sz)
dist_s0 = f"{k0['dist']:.0f} km" if k0["dist"] is not None else "—"
time_s0 = f"{k0['time_h']:.1f} h" if k0["time_h"] is not None else "—"
stops_s0 = f"{k0['stops']}" if rts0 else "—"
truck_s0 = str(k0["trucks"])

# KPI row at the top of the dashboard.
st.markdown(
    f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-emoji">🚚</div>
    <div class="kpi-t">Active trucks</div>
    <div class="kpi-v">{truck_s0}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-emoji">📦</div>
    <div class="kpi-t">Total stops (primary)</div>
    <div class="kpi-v">{stops_s0}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-emoji">⏱</div>
    <div class="kpi-t">Est. time @ 40 km/h</div>
    <div class="kpi-v">{time_s0}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-emoji">📏</div>
    <div class="kpi-t">Total distance (best)</div>
    <div class="kpi-v">{dist_s0}</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Three-column layout: controls, map, and route details.
c_left, c_mid, c_right = st.columns([0.88, 1.55, 0.9], gap="large")

with c_left:
    # Left panel: controls and route computation trigger.
    st.markdown('<p class="sec-t">Controls</p>', unsafe_allow_html=True)
    st.divider()
    traffic = st.slider("Traffic load", 1.0, 2.0, 1.0, 0.05, help="Scales all road weights.")
    g = build_graph(traffic)
    cities = list(g.graph.keys())
    truck_count = st.slider("Fleet size (trucks)", 1, 3, 2, key="fleet_sz")
    sim_step = st.slider(
        "Simulation speed (seconds per stop)",
        0.3,
        2.0,
        1.0,
        0.1,
        key="sim_step_sec",
        help="Slower = easier to read each step. Used for live delivery animation.",
    )
    st.markdown("**Locations**", unsafe_allow_html=True)
    warehouse = st.selectbox("Warehouse", cities, index=0)
    source_input = st.text_input("Source", placeholder="Enter place name or lat,lon in India")
    destination_input = st.text_input("Destination", placeholder="Enter place name or lat,lon in India")
    st.caption("If geocoding is unavailable, use coordinates like 23.3441,86.3397.")
    st.caption("Recompute after changing traffic or locations.")
    run = st.button("Compute routes", type="primary", use_container_width=True)
    source = _normalize_city_name(source_input)
    destination = _normalize_city_name(destination_input)
    city_coords = dict(BASE_CITY_COORDS)
    source_coords: Optional[Tuple[float, float]] = BASE_CITY_COORDS.get(source)
    destination_coords: Optional[Tuple[float, float]] = BASE_CITY_COORDS.get(destination)
    if run:
        # Reset simulation flags for a fresh run.
        st.session_state.pending_sim = False
        st.session_state.replay_sim = False
        if not source or not destination:
            st.error("Source and destination cannot be empty.")
            st.session_state.routes_result = None
            st.session_state.route_edges_list = None
        elif source == destination:
            st.error("Source and destination must differ.")
            st.session_state.routes_result = None
            st.session_state.route_edges_list = None
        else:
            if source_coords is None:
                with st.spinner("Locating source..."):
                    source_coords, source_geocode_error = safe_geocode_india_location(source)
                if source_geocode_error:
                    st.error(source_geocode_error)
                    st.session_state.routes_result = None
                    st.session_state.route_edges_list = None
                    st.stop()
            if source_coords is None:
                st.error("Invalid source location. Please enter a valid location in India.")
                st.session_state.routes_result = None
                st.session_state.route_edges_list = None
                st.stop()
            if destination_coords is None:
                with st.spinner("Locating destination..."):
                    destination_coords, destination_geocode_error = safe_geocode_india_location(destination)
                if destination_geocode_error:
                    st.error(destination_geocode_error)
                    st.session_state.routes_result = None
                    st.session_state.route_edges_list = None
                    st.stop()
            if destination_coords is None:
                st.error("Invalid destination location. Please enter a valid location in India.")
                st.session_state.routes_result = None
                st.session_state.route_edges_list = None
                st.stop()
            source_connected = True
            destination_connected = True
            source_fallback_link = False
            destination_fallback_link = False
            if source not in BASE_CITY_COORDS:
                source_connected, source_fallback_link = extend_graph_with_location(
                    g, city_coords, source, source_coords, traffic
                )
            if destination not in BASE_CITY_COORDS:
                destination_connected, destination_fallback_link = extend_graph_with_location(
                    g, city_coords, destination, destination_coords, traffic
                )
            if not source_connected or not destination_connected:
                st.error(
                    "Could not connect one or more entered locations to nearby cities. "
                    "Try a location closer to the NCR network."
                )
                st.session_state.routes_result = None
                st.session_state.route_edges_list = None
                st.stop()
            if source_fallback_link or destination_fallback_link:
                st.warning(
                    "One or more locations were linked via the nearest city because no city was found within "
                    f"{int(NEARBY_CONNECTION_THRESHOLD_KM)} km."
                )
            routes = compute_fleet_routes(g, source, destination, truck_count)
            if not routes:
                st.error("No valid route found between source and destination.")
                st.session_state.routes_result = None
                st.session_state.route_edges_list = None
            else:
                # Warn when graph topology cannot provide enough unique paths.
                if truck_count > 1 and len(routes) < truck_count:
                    st.warning(
                        f"Only {len(routes)} distinct route(s) could be found for this pair. "
                        "Some areas may be bridges with no second path."
                    )
                st.session_state.routes_result = routes
                st.session_state.route_edges_list = [path_to_edges(p) for p, _d in routes]
                st.session_state.city_coords_map = city_coords
                st.session_state.pending_sim = True
                st.rerun()

if "city_coords_map" not in st.session_state:
    st.session_state.city_coords_map = dict(BASE_CITY_COORDS)

# Derived view state reused across middle and right panels.
rts = st.session_state.routes_result
el_list = st.session_state.route_edges_list
n_r = len(rts) if rts else 0

with c_mid:
    # Middle panel: interactive map with route highlighting.
    st.markdown('<p class="sec-t">Network map</p>', unsafe_allow_html=True)
    st.divider()
    highlight_idx = 0
    if n_r > 1:
        highlight_idx = st.radio(
            "Select truck to highlight",
            list(range(n_r)),
            format_func=lambda i: f"Truck {i + 1}",
            horizontal=True,
            key="truck_hl",
        )
    elif n_r == 1:
        highlight_idx = 0
    if n_r and n_r > 1:
        st.caption("Non-selected truck routes are drawn muted. Change selection to re-focus the map.")
    st.markdown(
        """
<div class="map-legend">🔵 Normal roads
· 🔴 Active route
· 🟢 Source
· 🟣 Destination
· 🟠 Warehouse
</div>
        """,
        unsafe_allow_html=True,
    )
    if el_list and rts and len(rts) == len(el_list):
        # Keep highlight index safe even if UI state gets stale.
        h = max(0, min(int(highlight_idx), len(rts) - 1))
        sel_edges = el_list[h]
        other_edges = [el_list[j] for j in range(len(el_list)) if j != h]
    else:
        sel_edges = None
        other_edges = None
    html_file = draw_graph(
        g,
        selected_route_edges=sel_edges,
        other_routes_edges=other_edges,
        source=source,
        destination=destination,
        warehouse=warehouse,
        node_positions=build_node_positions(st.session_state.get("city_coords_map", BASE_CITY_COORDS)),
        height=f"{MAP_IFRAME_HEIGHT}px",
    )
    with open(html_file, "r", encoding="utf-8") as f:
        map_html = f.read()
    components.html(
        map_html,
        width=None,
        height=MAP_IFRAME_HEIGHT,
        scrolling=True,
    )
    st.caption("Scroll inside the map if needed · Hover edges: Distance: X km")

with c_right:
    # Right panel: route cards and quick performance comparison.
    st.markdown('<p class="sec-t">Routes &amp; performance</p>', unsafe_allow_html=True)
    st.divider()
    if rts and el_list:
        st.markdown("**Route comparison**", unsafe_allow_html=True)
        for i, (path_nodes, d_km) in enumerate(rts):
            line = " → ".join(path_nodes)
            t_h = d_km / 40.0
            role = "Truck 1 (Best)" if i == 0 else f"Truck {i + 1} (Alternative)"
            if i == 0:
                # Best route gets visual emphasis.
                st.markdown(
                    f"""
<div class="rc-best">
  <div class="rc-t">{role}</div>
  <div class="rc-path">{line}</div>
  <p style="margin:0.5rem 0 0; font-size:0.86rem; color:#166534">Total distance: <b>{d_km} km</b> · Est. time: <b>{t_h:.1f} h</b> @ 40 km/h</p>
</div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
<div class="rc-alt">
  <div class="rc-t">{role}</div>
  <div class="rc-path">{line}</div>
  <p style="margin:0.5rem 0 0; font-size:0.86rem; color:#334155">Total distance: <b>{d_km} km</b> · Est. time: <b>{t_h:.1f} h</b> @ 40 km/h</p>
</div>
                    """,
                    unsafe_allow_html=True,
                )
        if st.button("Replay delivery simulation", use_container_width=True, key="replay"):
            st.session_state.replay_sim = True
            st.rerun()
    else:
        st.info("Run **Compute routes** to see routes, times, and map highlights.")

# Bottom expander: simple step-by-step route playback.
if (st.session_state.get("pending_sim") or st.session_state.get("replay_sim")) and st.session_state.routes_result:
    st.session_state.pending_sim = False
    st.session_state.replay_sim = False
    with st.expander("Live delivery simulation", expanded=True):
        step_sec = float(st.session_state.get("sim_step_sec", 1.0))
        st.caption(
            f"Follows the highlighted truck on the map (or Truck 1 if a single route). "
            f"Interval: {step_sec:.1f} s per stop (set under Controls)."
        )
        rts_sim = st.session_state.routes_result
        tidx = 0
        if rts_sim and len(rts_sim) > 1 and "truck_hl" in st.session_state:
            tidx = int(st.session_state["truck_hl"])
        # Guard against out-of-range highlight values after reruns.
        tidx = max(0, min(tidx, len(rts_sim) - 1))
        sim_path = rts_sim[tidx][0]
        nst = len(sim_path)
        bar = st.progress(0, text="Preparing run…")
        line = st.empty()
        for i, city in enumerate(sim_path):
            line.markdown(
                f"🚚 Truck {tidx + 1} reached **{city}**  —  step {i + 1} of {nst}"
            )
            bar.progress((i + 1) / nst, text=f"Progress: {i + 1}/{nst} — {city}")
            time.sleep(step_sec)
        bar.progress(1.0, text="Arrived at destination")
        line.empty()
        st.success(f"Leg complete. Truck {tidx + 1} path: {' → '.join(sim_path)}")