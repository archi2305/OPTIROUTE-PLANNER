'''location/city=node
road=edges
distance =weight'''


class Graph:
    #when new graph create automatically invoked
    def __init__(self):
        self.graph={}

    #add location
    def add_location(self,node):
        if node not in self.graph:
            self.graph[node]=[]

    #add roads from and to node1<->node2
    def add_road(self,node1,node2,distance):
        self.graph[node1].append((node2,distance))
        self.graph[node2].append((node1,distance))   

 #give nearest location to current location
    def get_neighbors(self,node):
        return self.graph[node]  

  