import networkx as nx
from pyvis.network import Network
import tempfile


def draw_graph(graph, highlight_path=None):

    G = nx.Graph()

    # Add edges to networkx
    for node in graph.graph:
        for neighbor, weight in graph.graph[node]:
            G.add_edge(node, neighbor, weight=weight)

    net = Network(
        height="650px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black"
    )

    # City positions (manual layout so map looks structured)
    positions = {
        "Delhi": (0, 0),
        "Noida": (200, 0),
        "Ghaziabad": (350, 50),
        "Meerut": (500, 100),
        "Gurgaon": (-200, -50),
        "Faridabad": (100, -150)
    }

    # Add nodes with fixed positions
    for node in G.nodes():
        x, y = positions.get(node, (0, 0))
        net.add_node(
            node,
            label=node,
            x=x,
            y=y,
            physics=False,
            size=25
        )

    # Add edges
    for source, target, data in G.edges(data=True):

        weight = data["weight"]

        color = "#3b82f6"
        width = 2

        if highlight_path:
            if (source, target) in highlight_path or (target, source) in highlight_path:
                color = "red"
                width = 5

        net.add_edge(
            source,
            target,
            label=str(weight),
            title=f"Distance: {weight} km",
            color=color,
            width=width
        )

    net.set_options("""
    {
      "nodes": {
        "font": {"size": 20}
      },
      "edges": {
        "font": {"size": 16},
        "smooth": false
      },
      "physics": {
        "enabled": false
      }
    }
    """)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.save_graph(temp_file.name)

    return temp_file.name