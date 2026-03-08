import heapq

def dijkstra(graph, start):

    distances = {node: float("inf") for node in graph.graph}
    previous = {node: None for node in graph.graph}

    distances[start] = 0

    pq = [(0, start)]

    while pq:

        current_distance, current_node = heapq.heappop(pq)

        for neighbor, weight in graph.get_neighbors(current_node):

            distance = current_distance + weight

            if distance < distances[neighbor]:

                distances[neighbor] = distance
                previous[neighbor] = current_node

                heapq.heappush(pq, (distance, neighbor))

    return distances, previous


def get_path(previous, start, end):

    path = []

    current = end

    while current is not None:

        path.append(current)
        current = previous[current]

    path.reverse()

    if path[0] == start:
        return path

    return []