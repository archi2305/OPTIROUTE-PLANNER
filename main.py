from algorithms.graph import Graph
from algorithms.bfs_dfs import bfs, dfs
from algorithms.scheduler import schedule_deliveries
from algorithms.dijkstra import dijkstra
from algorithms.delivery import Delivery
from algorithms.delivery_manager import DeliveryManager
from algorithms.backtracking import validate_routes
g=Graph()
manager = DeliveryManager()

d1 = Delivery(101, "B", 1, 5)
d2 = Delivery(102, "C", 2, 3)

manager.add_delivery(d1)
manager.add_delivery(d2)
schedule_deliveries(manager.deliveries)
manager.show_deliveries()
g.add_location("A")
g.add_location("B")
g.add_location("C")
g.add_location("D")

g.add_road("A","B",5)
g.add_road("A", "C", 1)
g.add_road("B", "D", 1)


print(g.graph)

print("BFS:")
bfs(g, "A")

print("DFS:")
dfs(g, "A")
distances = dijkstra(g, "A")

print("Shortest distances from warehouse A:")

for location, distance in distances.items():
    print(location, ":", distance)

for delivery in manager.deliveries:
    distance = distances[delivery.destination]

    print(f"Order {delivery.order_id} → {delivery.destination} (Distance {distance})")    

validate_routes(g, "A", manager.deliveries)    