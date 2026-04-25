import time

import streamlit as st
import streamlit.components.v1 as components

from algorithms.dijkstra import dijkstra
from algorithms.graph import Graph
from algorithms.visualizer import draw_graph

st.set_page_config(
    page_title="OptiRoute · Command Center",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700&display=swap" rel="stylesheet" />
<style>
  .block-container { padding-top: 0.75rem; padding-bottom: 2rem; max-width: 1680px; }
  h1, h2, h3, p, label { font-family: "Plus Jakarta Sans", system-ui, sans-serif !important; }
  .or-title { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.03em; color: #0f172a; margin: 0; }
  .or-sub { color: #64748b; font-size: 0.95rem; margin: 0.25rem 0 0.75rem; }
  .or-badge {
    display: inline-block; background: linear-gradient(135deg, #0d9488, #0ea5e9); color: #fff;
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
    padding: 0.25rem 0.5rem; border-radius: 6px; margin-right: 0.5rem; vertical-align: middle;
  }
  .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.85rem; margin: 0.4rem 0 1.1rem; }
  @media (max-width: 1100px) { .kpi-row { grid-template-columns: repeat(2, 1fr); } }
  .kpi-card {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1rem 1.1rem;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.07);
  }
  .kpi-emoji { font-size: 1.25rem; line-height: 1; }
  .kpi-t { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: #64748b; margin: 0.4rem 0 0.2rem; }
  .kpi-v { font-size: 1.4rem; font-weight: 700; color: #0f172a; }
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

if "routes_result" not in st.session_state:
    st.session_state.routes_result = None
if "route_edges_list" not in st.session_state:
    st.session_state.route_edges_list = None
if "pending_sim" not in st.session_state:
    st.session_state.pending_sim = False
if "replay_sim" not in st.session_state:
    st.session_state.replay_sim = False
if "fleet_sz" not in st.session_state:
    st.session_state.fleet_sz = 2


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


def path_to_edges(path: list) -> list:
    if len(path) < 2:
        return []
    return [(path[i], path[i + 1]) for i in range(len(path) - 1)]


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


rts0 = st.session_state.routes_result
f_sz = int(st.session_state.get("fleet_sz", 2))
k0 = kpi_value(rts0, f_sz)
dist_s0 = f"{k0['dist']:.0f} km" if k0["dist"] is not None else "—"
time_s0 = f"{k0['time_h']:.1f} h" if k0["time_h"] is not None else "—"
stops_s0 = f"{k0['stops']}" if rts0 else "—"
truck_s0 = str(k0["trucks"])

st.markdown(
    """
<p style="margin:0.25rem 0 0.5rem">
  <span class="or-badge">Live ops</span>
  <span class="or-title">Logistics control dashboard</span>
</p>
<p class="or-sub">Fleet routing on the NCR network — Dijkstra shortest path, per-truck map highlights, and live delivery steps.</p>
""",
    unsafe_allow_html=True,
)

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

st.markdown("<br/>", unsafe_allow_html=True)

c_left, c_mid, c_right = st.columns([0.88, 1.55, 0.9], gap="large")

with c_left:
    st.markdown('<p class="sec-t">Controls</p>', unsafe_allow_html=True)
    st.divider()
    traffic = st.slider("Traffic load", 1.0, 2.0, 1.0, 0.05, help="Scales all road weights.")
    g = build_graph(traffic)
    cities = list(g.graph.keys())
    truck_count = st.slider("Fleet size (trucks)", 1, 3, 2, key="fleet_sz")
    st.markdown("**Locations**", unsafe_allow_html=True)
    warehouse = st.selectbox("Warehouse", cities, index=0)
    source = st.selectbox("Source", cities, index=0)
    destination = st.selectbox("Destination", cities, index=1 if len(cities) > 1 else 0)
    st.caption("Recompute after changing traffic or locations.")
    run = st.button("Compute routes", type="primary", use_container_width=True)
    if run:
        st.session_state.pending_sim = False
        st.session_state.replay_sim = False
        if source == destination:
            st.error("Source and destination must differ.")
            st.session_state.routes_result = None
            st.session_state.route_edges_list = None
        else:
            routes: list = []
            dist, prev = dijkstra(g, source)
            path: list = []
            cur = destination
            while cur is not None:
                path.append(cur)
                cur = prev[cur]
            d_best = dist[destination]
            routes.append((path, d_best))
            g2 = build_graph(traffic)
            if truck_count > 1 and len(path) > 2:
                r1, r2 = path[0], path[1]
                g2.graph[r1] = [(n, w) for n, w in g2.graph[r1] if n != r2]
                d2, pr2 = dijkstra(g2, source)
                p2: list = []
                c2 = destination
                while c2 is not None:
                    p2.append(c2)
                    c2 = pr2[c2]
                p2.reverse()
                routes.append((p2, d2[destination]))
            st.session_state.routes_result = routes
            st.session_state.route_edges_list = [path_to_edges(p) for p, _d in routes]
            st.session_state.pending_sim = True
            st.rerun()

# Refresh derived state
rts = st.session_state.routes_result
el_list = st.session_state.route_edges_list
n_r = len(rts) if rts else 0

with c_mid:
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
    st.markdown("<br/>", unsafe_allow_html=True)
    if el_list and rts and len(rts) == len(el_list):
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
    )
    with open(html_file, "r", encoding="utf-8") as f:
        map_html = f.read()
    components.html(map_html, height=700, scrolling=True)
    st.caption("Hover an edge to see: Distance: X km")

with c_right:
    st.markdown('<p class="sec-t">Routes &amp; performance</p>', unsafe_allow_html=True)
    st.divider()
    if rts and el_list:
        st.markdown("**Route comparison**", unsafe_allow_html=True)
        for i, (path_nodes, d_km) in enumerate(rts):
            line = " → ".join(path_nodes)
            t_h = d_km / 40.0
            if i == 0:
                st.markdown(
                    f"""
<div class="rc-best">
  <div class="rc-t">Truck {i + 1} (best)</div>
  <div class="rc-path">{line}</div>
  <p style="margin:0.5rem 0 0; font-size:0.86rem; color:#166534">Distance: <b>{d_km} km</b> · Est. time: <b>{t_h:.1f} h</b> @ 40 km/h</p>
</div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
<div class="rc-alt">
  <div class="rc-t">Truck {i + 1} (alternative)</div>
  <div class="rc-path">{line}</div>
  <p style="margin:0.5rem 0 0; font-size:0.86rem; color:#334155">Distance: <b>{d_km} km</b> · Est. time: <b>{t_h:.1f} h</b> @ 40 km/h</p>
</div>
                    """,
                    unsafe_allow_html=True,
                )
        if st.button("Replay delivery simulation", use_container_width=True, key="replay"):
            st.session_state.replay_sim = True
            st.rerun()
    else:
        st.info("Run **Compute routes** to see routes, times, and map highlights.")

st.markdown("<br/>", unsafe_allow_html=True)
if (st.session_state.get("pending_sim") or st.session_state.get("replay_sim")) and st.session_state.routes_result:
    st.session_state.pending_sim = False
    st.session_state.replay_sim = False
    st.markdown('<p class="sec-t">Live delivery simulation</p>', unsafe_allow_html=True)
    st.caption("Animates the highlighted truck’s route. Use 0.65 s per stop — adjust the pause in the code to taste.")
    rts_sim = st.session_state.routes_result
    tidx = 0
    if rts_sim and len(rts_sim) > 1 and "truck_hl" in st.session_state:
        tidx = int(st.session_state["truck_hl"])
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
        time.sleep(0.65)
    bar.progress(1.0, text="Arrived at destination")
    line.empty()
    st.success(f"Leg complete. Truck {tidx + 1} path: {' → '.join(sim_path)}")