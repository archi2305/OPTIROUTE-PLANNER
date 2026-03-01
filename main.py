from algorithms.graph import Graph
g=Graph()

g.add_location("A")
g.add_location("B")
g.add_location("C")

g.add_road("A","B",5)
g.add_road("B","A",2)

print(g.graph)

