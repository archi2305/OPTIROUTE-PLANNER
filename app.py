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
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;1,500&display=swap" rel="stylesheet" />
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1280px; }
    h1, h2, h3, p, span, label, [data-baseweb] { font-family: "Plus Jakarta Sans", system-ui, sans-serif !important; }
    .or-hero h1 { font-size: 2.15rem; font-weight: 700; letter-spacing: -0.03em; color: #0f172a; margin: 0 0 0.35rem; }
    .or-hero p { color: #64748b; font-size: 1.05rem; max-width: 40rem; margin: 0 0 0.2rem; line-height: 1.5; }
    .or-badge { display: inline-block; background: linear-gradient(135deg, #0d9488 0%, #0ea5e9 100%);
      color: white; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
      padding: 0.28rem 0.6rem; border-radius: 6px; margin-bottom: 0.75rem; }
    .or-legend { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin: 1rem 0 0.5rem; }
    .or-pill { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; font-weight: 500; padding: 0.3rem 0.7rem; border-radius: 9999px; border: 1px solid #e2e8f0; background: #f8fafc; color: #334155; }
    .or-pill b { display: inline-block; width: 0.5rem; height: 0.5rem; border-radius: 50%; }
    div[data-testid="stSidebar"] h2 { font-size: 1.05rem; font-weight: 600; color: #0f172a; }
</style>
""",
    unsafe_allow_html=True,
)

if "path_edges" not in st.session_state:
    st.session_state.path_edges = None
if "routes_result" not in st.session_state:
    st.session_state.routes_result = None
if "pending_sim" not in st.session_state:
    st.session_state.pending_sim = False


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


with st.sidebar:
    st.markdown("## Scenario")
    traffic = st.slider(
        "Traffic load multiplier",
        1.0,
        2.0,
        1.0,
        0.05,
        help="Scales all segment weights to simulate heavier traffic.",
    )

g = build_graph(traffic)
cities = list(g.graph.keys())

with st.sidebar:
    truck_count = st.slider("Fleet size (trucks)", 1, 3, 2, help="Request a primary route; optional second path when more than one truck and path length > 2.")
    st.divider()
    st.markdown("## Nodes")
    warehouse = st.selectbox("Hub / warehouse", cities, index=0)
    source = st.selectbox("Origin", cities, index=0)
    destination = st.selectbox("Destination", cities, index=1 if len(cities) > 1 else 0)
    st.caption("Adjust weights or endpoints, then compute again to refresh results.")

st.markdown(
    """
<div class="or-hero">
  <div class="or-badge">NCR logistics · Dijkstra</div>
  <h1>OptiRoute command center</h1>
  <p>Model the national capital region network, run shortest-path routing, and review fleet alternatives with an interactive map.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="or-legend">
  <span class="or-pill"><b style="background:#f43f5e;"></b> Shortest path</span>
  <span class="or-pill"><b style="background:#64748b;"></b> Other links</span>
  <span class="or-pill"><b style="background:#059669;"></b> Origin</span>
  <span class="or-pill"><b style="background:#7c3aed;"></b> Destination</span>
  <span class="or-pill"><b style="background:#d97706;"></b> Hub</span>
  <span class="or-pill"><b style="background:#0ea5e9;"></b> Waypoint on path</span>
</div>
""",
    unsafe_allow_html=True,
)

col_map, col_insight = st.columns([1.65, 1], gap="large")

html_path = st.session_state.path_edges if st.session_state.routes_result is not None else None
html_file = draw_graph(
    g,
    highlight_path=html_path,
    source=source,
    destination=destination,
    warehouse=warehouse,
)
with open(html_file, "r", encoding="utf-8") as f:
    map_html = f.read()

with col_map:
    with st.container(border=True):
        st.caption("Live network")
        st.markdown("Pan and zoom, hover **edges** for segment length (km).")
        components.html(map_html, height=700, scrolling=True)

with col_insight:
    st.subheader("Dispatch")
    run = st.button("Compute shortest routes", type="primary", use_container_width=True)
    if run:
        st.session_state.pending_sim = False
        if source == destination:
            st.error("Origin and destination must differ.")
            st.session_state.path_edges = None
            st.session_state.routes_result = None
        else:
            routes = []
            dist, prev = dijkstra(g, source)
            path: list = []
            current = destination
            while current is not None:
                path.append(current)
                current = prev[current]
            path.reverse()
            best_distance = dist[destination]
            routes.append((path, best_distance))
            g2 = build_graph(traffic)
            if truck_count > 1 and len(path) > 2:
                remove_city1, remove_city2 = path[0], path[1]
                g2.graph[remove_city1] = [
                    (n, w) for n, w in g2.graph[remove_city1] if n != remove_city2
                ]
                dist2, prev2 = dijkstra(g2, source)
                path2: list = []
                cur = destination
                while cur is not None:
                    path2.append(cur)
                    cur = prev2[cur]
                path2.reverse()
                alt_distance = dist2[destination]
                routes.append((path2, alt_distance))

            st.session_state.routes_result = routes
            best_path = routes[0][0]
            edges = []
            for i in range(len(best_path) - 1):
                edges.append((best_path[i], best_path[i + 1]))
            st.session_state.path_edges = edges
            st.session_state.pending_sim = True
            st.rerun()

    if st.session_state.routes_result:
        rts = st.session_state.routes_result
        best = rts[0]
        hops = len(best[0]) - 1
        st.metric("Shortest distance", f"{best[1]} km")
        if len(rts) > 1:
            st.caption("A second option is available for another truck.")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Stops (edges)", f"{hops}")
        with c2:
            est_h = best[1] / 40.0
            st.metric("Est. time @ 40 km/h", f"{est_h:.1f} h")

        st.subheader("Ordered routes")
        for i, (route, d) in enumerate(rts):
            line = " → ".join(route)
            if i == 0:
                st.success(f"**Truck {i + 1}** (optimal) · {d} km  \n{line}")
            else:
                st.info(f"**Truck {i + 1}** (alternative) · {d} km  \n{line}")
    else:
        st.info("Set origin and destination, then run **Compute** to highlight the shortest path and show metrics.")

if st.session_state.pending_sim and st.session_state.routes_result and st.session_state.path_edges:
    st.divider()
    best_path = st.session_state.routes_result[0][0]
    st.session_state.pending_sim = False
    with st.status("Delivery simulation (step-through)", expanded=True) as status:
        for i, city in enumerate(best_path):
            st.write(f"**Checkpoint {i + 1}/{len(best_path)}** — {city}")
            time.sleep(0.45)
        status.update(label="Simulation complete", state="complete")
