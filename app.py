import streamlit as st
from algorithms.graph import Graph
from algorithms.delivery import Delivery
from algorithms.delivery_manager import DeliveryManager
from algorithms.scheduler import schedule_deliveries
from algorithms.dijkstra import dijkstra

st.title("🚚 OptiRoute Planner")


# Persistent Storage

if "graph" not in st.session_state:
    st.session_state.graph = Graph()

if "manager" not in st.session_state:
    st.session_state.manager = DeliveryManager()

g = st.session_state.graph
manager = st.session_state.manager


# Add Location

st.header("Add Location")

location = st.text_input("Location Name").strip().lower()

if st.button("Add Location", key="add_location"):
    if location:
        g.add_location(location)
        st.success(f"{location} added to map")
    else:
        st.error("Enter location name")


# Add Road

st.header("Add Road")

node1 = st.text_input("From").strip().lower()
node2 = st.text_input("To").strip().lower()
distance = st.number_input("Distance", min_value=1)

if st.button("Add Road", key="add_road"):
    if node1 and node2:
        g.add_road(node1, node2, distance)
        st.success(f"Road added: {node1} ↔ {node2}")
    else:
        st.error("Enter both locations")


# Add Delivery

st.header("Add Delivery")

order_id = st.number_input("Order ID", min_value=1)
destination = st.text_input("Destination").strip().lower()
priority = st.number_input("Priority", min_value=1)
deadline = st.number_input("Deadline", min_value=1)

if st.button("Add Delivery", key="add_delivery"):
    if destination:
        d = Delivery(order_id, destination, priority, deadline)
        manager.add_delivery(d)
        st.success("Delivery Added")
    else:
        st.error("Enter destination")


# Show Deliveries

st.header("Current Deliveries")

if manager.deliveries:
    for d in manager.deliveries:
        st.write(
            f"Order {d.order_id} → {d.destination} | Priority {d.priority} | Deadline {d.deadline}"
        )
else:
    st.write("No deliveries yet.")


# Schedule Deliveries

st.header("Schedule Deliveries")

if st.button("Schedule Deliveries", key="schedule"):
    if manager.deliveries:
        sorted_deliveries = schedule_deliveries(manager.deliveries)

        st.subheader("Delivery Order")
        for d in sorted_deliveries:
            st.write(f"Order {d.order_id} → {d.destination}")
    else:
        st.warning("No deliveries to schedule")


# Compute Shortest Routes

st.header("Compute Shortest Routes")

start = st.text_input("Warehouse Location").strip().lower()

if st.button("Compute Routes", key="compute_routes"):

    if not start:
        st.error("Please enter warehouse location")

    elif start not in g.graph:
        st.error("Warehouse location does not exist in the map.")

    else:
        distances = dijkstra(g, start)

        st.subheader("Shortest Distances")

        for loc, dist in distances.items():
            st.write(f"{start} → {loc} : {dist}")

        if manager.deliveries:
            st.subheader("Delivery Routes")

            for d in manager.deliveries:
                if d.destination in distances:
                    st.write(
                        f"Order {d.order_id} → {d.destination} | Distance {distances[d.destination]}"
                    )


# Debug Section

st.header("Current Map")

st.write("Locations:", list(g.graph.keys()))