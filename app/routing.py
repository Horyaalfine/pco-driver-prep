"""
Pure graph logic for topographical route-planning scenarios: no Flask, no DB
session — just map data in, score out. Kept separate from app/learning.py so
it's easy to unit-test on its own.
"""
import heapq


def build_adjacency(map_data: dict) -> dict:
    """Turn a RouteMap.data dict into a directed adjacency list:
    {node_id: [(neighbour_id, weight, edge_name), ...], ...}
    A two-way edge (oneway is None/absent) produces an entry in both
    directions; a one-way edge produces only the allowed direction."""
    adjacency = {node_id: [] for node_id in map_data["nodes"]}
    for edge in map_data["edges"]:
        a, b = edge["from"], edge["to"]
        weight = edge.get("weight", 1)
        name = edge.get("name", "")
        oneway = edge.get("oneway")
        if oneway == "reverse":
            adjacency[b].append((a, weight, name))
        elif oneway == "forward":
            adjacency[a].append((b, weight, name))
        else:
            adjacency[a].append((b, weight, name))
            adjacency[b].append((a, weight, name))
    return adjacency


def shortest_legal_path(adjacency: dict, start: str, end: str):
    """Dijkstra over the directed adjacency list. Returns (distance, path) —
    path as a list of node ids from start to end — or (None, None) if end is
    unreachable from start respecting one-way restrictions."""
    distances = {start: 0}
    previous = {}
    visited = set()
    heap = [(0, start)]
    while heap:
        dist, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if node == end:
            path = [end]
            while path[-1] != start:
                path.append(previous[path[-1]])
            path.reverse()
            return dist, path
        for neighbour, weight, _name in adjacency.get(node, []):
            new_dist = dist + weight
            if neighbour not in distances or new_dist < distances[neighbour]:
                distances[neighbour] = new_dist
                previous[neighbour] = node
                heapq.heappush(heap, (new_dist, neighbour))
    return None, None


def shortest_legal_length(adjacency: dict, start: str, end: str):
    """Convenience wrapper around shortest_legal_path for when only the
    distance is needed."""
    dist, _path = shortest_legal_path(adjacency, start, end)
    return dist


def score_route(map_data: dict, start: str, end: str, submitted_path: list) -> dict:
    """Validate and score a submitted path (list of node ids) against the
    map's one-way rules and the shortest legal route.

    Returns a dict:
      is_legal: bool — does every step exist and respect one-way direction?
      is_optimal: bool — if legal, does it match the shortest legal length?
      score_percent: 0-100
      submitted_length / optimal_length: for display
      message: human-readable feedback
      failed_at_step: index of the first illegal step, if any (else None)
    """
    adjacency = build_adjacency(map_data)
    optimal, optimal_path = shortest_legal_path(adjacency, start, end)

    if not submitted_path or submitted_path[0] != start:
        return {
            "is_legal": False, "is_optimal": False, "score_percent": 0.0,
            "submitted_length": None, "optimal_length": optimal, "optimal_path": optimal_path,
            "failed_at_step": 0,
            "message": "Your route must start at the given starting point.",
        }
    if submitted_path[-1] != end:
        return {
            "is_legal": False, "is_optimal": False, "score_percent": 0.0,
            "submitted_length": None, "optimal_length": optimal, "optimal_path": optimal_path,
            "failed_at_step": len(submitted_path) - 1,
            "message": "Your route doesn't reach the destination.",
        }

    total = 0
    for i in range(len(submitted_path) - 1):
        a, b = submitted_path[i], submitted_path[i + 1]
        edge = next((e for e in adjacency.get(a, []) if e[0] == b), None)
        if edge is None:
            # Distinguish "no street at all" from "street exists but you went
            # the wrong way down a one-way" for clearer feedback.
            reverse_exists = any(e[0] == a for e in adjacency.get(b, []))
            if reverse_exists:
                msg = "That street is one-way in the other direction at that point — you can't travel that way down it."
            else:
                msg = "There's no direct street connecting those two points on the map."
            return {
                "is_legal": False, "is_optimal": False, "score_percent": 0.0,
                "submitted_length": None,
                "optimal_length": optimal, "optimal_path": optimal_path,
                "failed_at_step": i,
                "message": msg,
            }
        total += edge[1]

    is_optimal = optimal is not None and total == optimal
    if is_optimal:
        score = 100.0
    elif optimal:
        # Legal but not the shortest — partial credit, floored at 40 so a
        # valid-but-roundabout route still reads as "you got there legally",
        # distinct from an illegal route (always 0).
        score = max(40.0, round(100.0 * optimal / total, 1))
    else:
        score = 40.0

    message = (
        "That's the most direct legal route."
        if is_optimal
        else f"Legal route, but not the most direct one — yours uses {total} street segment(s); "
             f"the most direct legal route uses {optimal}."
    )
    return {
        "is_legal": True,
        "is_optimal": is_optimal,
        "score_percent": score,
        "submitted_length": total,
        "optimal_length": optimal,
        "optimal_path": optimal_path,
        "failed_at_step": None,
        "message": message,
    }
