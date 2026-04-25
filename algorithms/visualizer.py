from pyvis.network import Network
import tempfile


def _edge_key(a, b):
    return (a, b) if a <= b else (b, a)


def draw_graph(
    g,
    highlight_path=None,
    source=None,
    destination=None,
    warehouse=None,
    height="680px",
):
    """
    Render the logistics network. highlight_path: list of (u, v) undirected edge pairs
    in either orientation.
    """
    net = Network(
        height=height,
        width="100%",
        directed=False,
        bgcolor="#0f172a",
        font_color="#e2e8f0",
    )

    path_nodes = set()
    if highlight_path:
        for u, v in highlight_path:
            path_nodes.add(u)
            path_nodes.add(v)
        path_edge_keys = {_edge_key(a, b) for a, b in highlight_path}
    else:
        path_edge_keys = set()

    positions = {
        "Delhi": (0, 0),
        "Noida": (200, 0),
        "Ghaziabad": (350, 50),
        "Meerut": (500, 0),
        "Gurgaon": (-150, -120),
        "Faridabad": (150, -120),
    }

    for city, (x, y) in positions.items():
        if city not in g.graph:
            continue

        border = "#334155"
        bg = "#475569"
        size = 28

        if city == source:
            bg = "#059669"
            border = "#34d399"
            size = 34
        elif city == destination:
            bg = "#7c3aed"
            border = "#a78bfa"
            size = 34
        elif warehouse and city == warehouse:
            bg = "#d97706"
            border = "#fbbf24"
            size = 32
        elif city in path_nodes and highlight_path:
            bg = "#0ea5e9"
            border = "#38bdf8"
            size = 30

        net.add_node(
            city,
            label=city,
            x=x,
            y=y,
            physics=False,
            size=size,
            color={"background": bg, "border": border, "highlight": {"background": bg, "border": "#f8fafc"}},
            borderWidth=2,
            font={"size": 16, "face": "ui-sans-serif, system-ui, sans-serif", "color": "#f8fafc"},
            title=f"Node: {city}",
        )

    seen_edges = set()
    for city in g.graph:
        for neighbor, weight in g.graph[city]:
            ek = _edge_key(city, neighbor)
            if ek in seen_edges:
                continue
            seen_edges.add(ek)

            on_path = highlight_path and (ek in path_edge_keys)

            if on_path:
                color = {"color": "#f43f5e", "highlight": "#fb7185"}
                width = 4
            else:
                color = {"color": "#475569", "highlight": "#64748b"}
                width = 2

            net.add_edge(
                city,
                neighbor,
                label=f"{weight}",
                color=color,
                width=width,
                title=f"{city} ↔ {neighbor} · {weight} km",
                font={"size": 12, "color": "#94a3b8", "strokeWidth": 0, "face": "ui-sans-serif, system-ui, sans-serif"},
            )

    net.set_options(
        """
    {
      "layout": { "hierarchical": { "enabled": false } },
      "interaction": { "hover": true, "tooltipDelay": 80, "zoomView": true, "dragView": true },
      "nodes": { "borderWidth": 2, "shadow": true, "font": { "size": 16, "face": "system-ui" } },
      "edges": {
        "shadow": { "enabled": true, "size": 3 },
        "smooth": { "type": "continuous", "roundness": 0.45 }
      },
      "physics": { "enabled": false }
    }
    """
    )

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.save_graph(temp_file.name)
    return temp_file.name
