import networkx as nx
from pyvis.network import Network
import tempfile


def draw_graph(graph, highlight_path=None):

    G = nx.Graph()

    for node in graph.graph:
        for neighbor, weight in graph.graph[node]:
            G.add_edge(node, neighbor, weight=weight)

    net = Network(
        height="600px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black"
    )

    net.barnes_hut()  # better layout physics

    for node in G.nodes():
        net.add_node(
            node,
            label=node,
            title=f"City: {node}",
            size=20
        )

    for u, v, data in G.edges(data=True):

        weight = data["weight"]

        color = "#97C2FC"
        width = 2

        if highlight_path:
            if (u, v) in highlight_path or (v, u) in highlight_path:
                color = "red"
                width = 5

        net.add_edge(
            u,
            v,
            label=str(weight),
            title=f"Distance: {weight} km",
            color=color,
            width=width
        )

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")

    net.save_graph(temp_file.name)

    return temp_file.name