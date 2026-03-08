def load_default_map(graph):

    roads = [
        ("delhi", "noida", 20),
        ("delhi", "gurgaon", 15),
        ("delhi", "ghaziabad", 18),
        ("delhi", "faridabad", 22),

        ("noida", "greater noida", 15),
        ("noida", "ghaziabad", 12),
        ("noida", "faridabad", 25),

        ("gurgaon", "manesar", 18),
        ("gurgaon", "faridabad", 10),

        ("faridabad", "palwal", 25),

        ("ghaziabad", "meerut", 45),

        ("greater noida", "bulandshahr", 40),

        ("manesar", "rewari", 35),

        ("palwal", "mathura", 50),

        ("meerut", "muzaffarnagar", 60),
    ]

    for city1, city2, dist in roads:
        graph.add_road(city1, city2, dist)