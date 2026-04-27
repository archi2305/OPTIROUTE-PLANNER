from pyvis.network import Network
import tempfile


def _edge_key(a, b):
    return (a, b) if a <= b else (b, a)


def _edges_to_keys(edges):
    if not edges:
        return set()
    return {_edge_key(a, b) for a, b in edges}


def draw_graph(
    g,
    selected_route_edges=None,
    other_routes_edges=None,
    source=None,
    destination=None,
    warehouse=None,
    node_positions=None,
    height="720px",
):
    # Build an interactive city network map.
    net = Network(
        height=height,
        width="100%",
        directed=False,
        bgcolor="#0B1A2B",
        font_color="#e2e8f0",
    )

    selected_keys = _edges_to_keys(selected_route_edges)
    other_key_sets = [_edges_to_keys(es) for es in (other_routes_edges or []) if es]
    other_keys = set()
    for s in other_key_sets:
        other_keys |= s
    other_keys -= selected_keys

    default_positions = {
        "Delhi": (0, 0),
        "Noida": (200, 0),
        "Ghaziabad": (350, 50),
        "Meerut": (500, 0),
        "Gurgaon": (-150, -120),
        "Faridabad": (150, -120),
    }
    positions = dict(default_positions)
    if node_positions:
        positions.update(node_positions)

    c_wh = "#f97316"
    c_src = "#22c55e"
    c_dst = "#a855f7"
    c_neutral = "#7dd3fc"

    for city in g.graph:
        x, y = positions.get(city, (0, 0))

        border = "#1e3a5f"
        bg = c_neutral
        size = 26

        if city == source:
            bg, border, size = c_src, "#4ade80", 34
        elif city == destination:
            bg, border, size = c_dst, "#c4b5fd", 34
        elif warehouse and city == warehouse:
            bg, border, size = c_wh, "#fdba74", 32

        net.add_node(
            city,
            label=city,
            x=x,
            y=y,
            physics=False,
            size=size,
            color={
                "background": bg,
                "border": border,
                "highlight": {"background": bg, "border": "#f8fafc"},
            },
            borderWidth=2,
            font={
                "size": 16,
                "face": "ui-sans-serif, system-ui, sans-serif",
                "color": "#f8fafc",
            },
            title=city,
        )

    # Track undirected edges so each road is drawn once.
    seen_edges = set()
    for city in g.graph:
        for neighbor, weight in g.graph[city]:
            ek = _edge_key(city, neighbor)
            if ek in seen_edges:
                continue
            seen_edges.add(ek)

            w_km = int(weight) if float(weight) == int(weight) else weight
            title = f"Distance: {w_km} km"

            if selected_route_edges and (ek in selected_keys):
                color = {"color": "#ff3333", "highlight": "#ff6b6b"}
                width = 6
            elif other_keys and (ek in other_keys):
                color = {"color": "#6b7d96", "highlight": "#94a3b8"}
                width = 2
            else:
                color = {"color": "#334a66", "highlight": "#475569"}
                width = 1

            net.add_edge(
                city,
                neighbor,
                label="" if width == 1 else f"{w_km}",
                color=color,
                width=width,
                title=title,
                font={
                    "size": 12,
                    "color": "#94a3b8",
                    "strokeWidth": 0,
                    "face": "ui-sans-serif, system-ui, sans-serif",
                },
            )

    net.set_options(
        """
    {
      "layout": { "hierarchical": { "enabled": false } },
      "interaction": { "hover": true, "tooltipDelay": 60, "zoomView": true, "dragView": true },
      "nodes": { "borderWidth": 2, "shadow": true, "font": { "size": 15, "face": "system-ui" } },
      "edges": {
        "shadow": { "enabled": true, "size": 2 },
        "smooth": { "type": "continuous", "roundness": 0.4 }
      },
      "physics": { "enabled": false }
    }
    """
    )

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.save_graph(temp_file.name)
    return temp_file.name
