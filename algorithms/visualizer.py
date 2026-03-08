from pyvis.network import Network
import tempfile

def draw_graph(g, highlight_path=None):

    net = Network(height="600px", width="100%", directed=False)

    positions = {
        "Delhi": (0, 0),
        "Noida": (200, 0),
        "Ghaziabad": (350, 50),
        "Meerut": (500, 0),
        "Gurgaon": (-150, -100),
        "Faridabad": (150, -120)
    }

    for city, (x, y) in positions.items():
        net.add_node(
            city,
            label=city,
            x=x,
            y=y,
            physics=False,
            size=25,
            color="#4A90E2"
        )

    for city in g.graph:
        for neighbor, weight in g.graph[city]:

            color = "blue"
            width = 2

            if highlight_path and ((city, neighbor) in highlight_path or (neighbor, city) in highlight_path):
                color = "red"
                width = 5

            net.add_edge(
                city,
                neighbor,
                label=str(weight),
                color=color,
                width=width,
                title=f"{city} → {neighbor} : {weight} km"
            )

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")

    net.save_graph(temp_file.name)

    return temp_file.name