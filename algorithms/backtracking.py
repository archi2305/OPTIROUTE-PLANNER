def validate_routes(graph, start, deliveries, path=None, visited=None):

    if path is None:
        path = []

    if visited is None:
        visited = set()

    if len(path) == len(deliveries):
        print("Valid delivery route:", path)
        return True

    for delivery in deliveries:
        if delivery.destination not in visited:

            visited.add(delivery.destination)
            path.append(delivery.destination)

            if validate_routes(graph, start, deliveries, path, visited):
                return True

            # backtrack
            visited.remove(delivery.destination)
            path.pop()

    return False