from algorithms.graph import Graph
from algorithms.bfs_dfs import bfs, dfs
g=Graph()

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