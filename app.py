import streamlit as st
import streamlit.components.v1 as components
import time

from algorithms.graph import Graph
from algorithms.dijkstra import dijkstra
from algorithms.visualizer import draw_graph

st.title("Logistics Route Optimization System")

st.info("🔵 Blue roads = Normal roads | 🔴 Red roads = Best Route")

traffic = st.slider("Traffic Level", 1.0, 2.0, 1.0)

truck_count = st.slider("Number of Delivery Trucks", 1, 3, 2)

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

cities = list(g.graph.keys())

warehouse = st.selectbox("Select Warehouse", cities)
source = st.selectbox("Select Source Location", cities)
destination = st.selectbox("Select Destination Location", cities)

if st.button("Compute Route"):

    if source == destination:
        st.error("Source and Destination cannot be the same.")
    else:

        routes = []

        dist, prev = dijkstra(g, source)

        path = []
        current = destination

        while current is not None:
            path.append(current)
            current = prev[current]

        path.reverse()

        best_distance = dist[destination]

        routes.append((path, best_distance))

        if truck_count > 1 and len(path) > 2:

            remove_city1 = path[0]
            remove_city2 = path[1]

            g.graph[remove_city1] = [
                (n, w) for n, w in g.graph[remove_city1] if n != remove_city2
            ]

            dist2, prev2 = dijkstra(g, source)

            path2 = []
            current = destination

            while current is not None:
                path2.append(current)
                current = prev2[current]

            path2.reverse()

            alt_distance = dist2[destination]

            routes.append((path2, alt_distance))

        st.subheader("Route Comparison")

        for i, (route, dist) in enumerate(routes):

            route_text = " → ".join(route)

            if i == 0:
                st.success(f"Truck {i+1} (Best): {route_text} | {dist} km")
            else:
                st.write(f"Truck {i+1}: {route_text} | {dist} km")

        best_path = routes[0][0]

        edges = []
        for i in range(len(best_path) - 1):
            edges.append((best_path[i], best_path[i + 1]))

        st.subheader("Delivery Simulation")

        progress_bar = st.progress(0)
        status = st.empty()

        for i, city in enumerate(best_path):

            percent = int((i + 1) / len(best_path) * 100)

            status.write(f"Truck reached: {city}")

            progress_bar.progress(percent)

            time.sleep(0.8)

        html_file = draw_graph(g, highlight_path=edges)

        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()

        st.subheader("Network Map")

        components.html(html, height=650)