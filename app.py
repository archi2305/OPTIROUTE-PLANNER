import streamlit as st
import streamlit.components.v1 as components

from algorithms.graph import Graph
from algorithms.dijkstra import dijkstra
from algorithms.visualizer import draw_graph

st.title("Logistics Route Optimization System")

st.info("🔵 Blue roads = Normal roads | 🔴 Red roads = Shortest path")

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
    g.add_road(c1, c2, d)

cities = list(g.graph.keys())

warehouse = st.selectbox("Select Warehouse", cities)
source = st.selectbox("Select Source Location", cities)
destination = st.selectbox("Select Destination Location", cities)

if st.button("Compute Route"):

    if source == destination:
        st.error("Source and Destination cannot be the same.")
    else:

        dist1, prev1 = dijkstra(g, warehouse)

        path1 = []
        current = source
        while current is not None:
            path1.append(current)
            current = prev1[current]
        path1.reverse()

        dist2, prev2 = dijkstra(g, source)

        path2 = []
        current = destination
        while current is not None:
            path2.append(current)
            current = prev2[current]
        path2.reverse()

        full_path = path1 + path2[1:]

        total_distance = dist1[source] + dist2[destination]

        avg_speed = 40
        estimated_time = total_distance / avg_speed
        estimated_time_minutes = round(estimated_time * 60)

        edges = []
        for i in range(len(full_path) - 1):
            edges.append((full_path[i], full_path[i+1]))

        st.subheader("Route Breakdown")

        for i in range(len(full_path) - 1):

            city1 = full_path[i]
            city2 = full_path[i+1]

            distance = None
            for neighbor, weight in g.graph[city1]:
                if neighbor == city2:
                    distance = weight
                    break

            st.write(f"{city1} → {city2} : {distance} km")

        html_file = draw_graph(g, highlight_path=edges)

        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()

        st.subheader("Network Map")
        components.html(html, height=650)

        st.subheader("Optimal Route")

        route = " → ".join(full_path)

        st.success(f"""
Warehouse: {warehouse}

Route: {route}

Total Distance: {total_distance} km

Estimated Delivery Time: {estimated_time_minutes} minutes
""")