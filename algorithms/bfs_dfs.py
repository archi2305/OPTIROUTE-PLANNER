from collections import deque
#creating bfs 
def bfs(graph,start):
        visited=set()
        queue=deque([start])     

        while queue:
            node=queue.popleft()

            if node not in visited:
                print(node)
                visited.add(node)

                for neighbor, _ in graph.get_neighbors(node):
                    if neighbor not in visited:

                        queue.append(neighbor) 

def dfs(graph, start, visited=None):
        if visited is None:
            visited = set()

        if start not in graph.graph:
            print("Node not found")
            return

        print(start)
        visited.add(start)

        for neighbor, _ in graph.get_neighbors(start):
            if neighbor not in visited:
                dfs(graph, neighbor, visited) 