import heapq
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ---------------------------------------------------------------- DATA
roads = {
    "Delhi": {"Jaipur": 280, "Lucknow": 550, "Chandigarh": 245, "Bhopal": 780},
    "Jaipur": {"Delhi": 280, "Ahmedabad": 660, "Mumbai": 1150, "Lucknow": 570},
    "Lucknow": {"Delhi": 550, "Jaipur": 570, "Kolkata": 990, "Bhopal": 585},
    "Chandigarh": {"Delhi": 245, "Ludhiana": 105, "Jaipur": 520},
    "Ludhiana": {"Chandigarh": 105, "Delhi": 310, "Srinagar": 430},
    "Srinagar": {"Ludhiana": 430, "Delhi": 810},
    "Ahmedabad": {"Jaipur": 660, "Mumbai": 530, "Bhopal": 580},
    "Mumbai": {"Jaipur": 1150, "Ahmedabad": 530, "Pune": 150, "Hyderabad": 710},
    "Pune": {"Mumbai": 150, "Bengaluru": 840, "Hyderabad": 560},
    "Bhopal": {"Delhi": 780, "Lucknow": 585, "Ahmedabad": 580, "Hyderabad": 850, "Nagpur": 350},
    "Nagpur": {"Bhopal": 350, "Hyderabad": 500, "Kolkata": 1100},
    "Hyderabad": {"Mumbai": 710, "Pune": 560, "Bhopal": 850, "Nagpur": 500, "Bengaluru": 570, "Chennai": 630},
    "Bengaluru": {"Pune": 840, "Hyderabad": 570, "Chennai": 350, "Kochi": 550},
    "Chennai": {"Hyderabad": 630, "Bengaluru": 350, "Kolkata": 1660},
    "Kochi": {"Bengaluru": 550},
    "Kolkata": {"Lucknow": 990, "Nagpur": 1100, "Chennai": 1660},
}

# Map coordinates (x, y) used by the frontend to draw the cities
positions = {
    "Srinagar": (1.4, 7.8), "Ludhiana": (2.0, 6.8), "Chandigarh": (2.8, 6.1),
    "Delhi": (3.8, 5.6), "Jaipur": (2.7, 4.8), "Lucknow": (5.4, 5.0),
    "Ahmedabad": (1.5, 3.5), "Bhopal": (4.2, 3.8), "Mumbai": (1.7, 2.2),
    "Pune": (2.8, 1.7), "Nagpur": (6.0, 3.1), "Kolkata": (8.0, 4.7),
    "Hyderabad": (5.1, 2.0), "Bengaluru": (4.2, 0.7), "Chennai": (6.2, 0.7),
    "Kochi": (3.3, -0.5),
}


def build_graph(raw):
    """Make every road two-way. If both directions are listed, keep the smaller."""
    graph = {city: {} for city in raw}
    for a, neighbours in raw.items():
        for b, d in neighbours.items():
            graph[a][b] = min(d, graph[a].get(b, float("inf")))
            graph.setdefault(b, {})[a] = min(d, graph.get(b, {}).get(a, float("inf")))
    return graph


graph = build_graph(roads)


# ----------------------------------------------------------- ALGORITHM
def dijkstra(graph, source, destination):
    distances = {city: float("inf") for city in graph}
    previous = {city: None for city in graph}
    distances[source] = 0
    priority_queue = [(0, source)]
    visited = set()

    while priority_queue:
        current_distance, current_city = heapq.heappop(priority_queue)
        if current_city in visited:
            continue
        visited.add(current_city)
        if current_city == destination:
            break
        for neighbour, distance in graph[current_city].items():
            new_distance = current_distance + distance
            if new_distance < distances[neighbour]:
                distances[neighbour] = new_distance
                previous[neighbour] = current_city
                heapq.heappush(priority_queue, (new_distance, neighbour))

    if distances[destination] == float("inf"):
        return None, float("inf")

    route, city = [], destination
    while city is not None:
        route.append(city)
        city = previous[city]
    route.reverse()
    return route, distances[destination]


# --------------------------------------------------------------- ROUTES
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/graph")
def api_graph():
    seen, edges = set(), []
    for a, neighbours in graph.items():
        for b, d in neighbours.items():
            key = tuple(sorted((a, b)))
            if key not in seen:
                seen.add(key)
                edges.append({"from": a, "to": b, "distance": d})
    return jsonify(cities=sorted(graph), positions=positions, edges=edges)


@app.route("/api/route")
def api_route():
    source = request.args.get("source", "").strip().title()
    destination = request.args.get("destination", "").strip().title()

    if source not in graph or destination not in graph:
        return jsonify(error="Invalid city name. Choose a city from the list."), 400
    if source == destination:
        return jsonify(error=f"Start and destination are both {source}. Choose two different cities."), 400

    route, total = dijkstra(graph, source, destination)
    if route is None:
        return jsonify(error=f"No route found between {source} and {destination}."), 404

    segments = [{"from": a, "to": b, "distance": graph[a][b]} for a, b in zip(route, route[1:])]
    return jsonify(route=route, total=total, segments=segments)


if __name__ == "__main__":
    app.run(debug=True)
