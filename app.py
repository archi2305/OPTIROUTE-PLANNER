import streamlit as st
import streamlit.components.v1 as components

from algorithms.graph import Graph
from algorithms.dijkstra import dijkstra, get_path
from algorithms.visualizer import draw_graph
from algorithms.map_data import load_default_map

st.title(" OptiRoute Planner")


# GRAPH INITIALIZATION


if "graph" not in st.session_state:
    st.session_state.graph = Graph()
    load_default_map(st.session_state.graph)

g = st.session_state.graph



# SHOW AVAILABLE LOCATIONS


st.header("Available Locations")

st.write(list(g.graph.keys()))



# ROUTE SELECTION


st.header("Route Planner")

warehouse = st.selectbox(
    "Select Warehouse Location",
    list(g.graph.keys()),
    key="warehouse_select"
)

destination = st.selectbox(
    "Select Delivery Destination",
    list(g.graph.keys()),
    key="destination_select"
)



# COMPUTE SHORTEST ROUTE


if st.button("Compute Shortest Route", key="compute_btn"):

    distances, previous = dijkstra(g, warehouse)

    path = get_path(previous, warehouse, destination)

    st.subheader("Shortest Route")

    st.write(" → ".join(path))

    st.subheader("Distance")

    st.write(distances[destination])

    # highlight path
    edges = list(zip(path, path[1:]))

    html_file = draw_graph(g, highlight_path=edges)

    HtmlFile = open(html_file, "r", encoding="utf-8")

    components.html(HtmlFile.read(), height=500)



# NETWORK MAP


st.header("City Network")

if st.button("Show Map", key="show_map_btn"):

    html_file = draw_graph(g)

    HtmlFile = open(html_file, "r", encoding="utf-8")

    components.html(HtmlFile.read(), height=500)