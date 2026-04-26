class Graph:
    # Simple adjacency list: city -> [(neighbor, distance), ...]
    def __init__(self):
        self.graph={}

    # Add a city only once.
    def add_location(self,node):
        if node not in self.graph:
            self.graph[node]=[]

    # Roads are undirected, so store both directions.
    def add_road(self, node1, node2, distance):

        if node1 not in self.graph:
            self.add_location(node1)

        if node2 not in self.graph:
            self.add_location(node2)

        self.graph[node1].append((node2, distance))
        self.graph[node2].append((node1, distance))   

    # Return all direct neighbors for a city.
    def get_neighbors(self,node):
        return self.graph[node]  

  