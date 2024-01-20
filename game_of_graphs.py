import sys

def read_file(file_path, is_conspiracy=False):
    relations = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(" is plotting against " if is_conspiracy else " is friends with ")
                if len(parts) == 2:
                    person1, person2 = parts
                    if person1 not in relations:
                        relations[person1] = set() if not is_conspiracy else []
                    if is_conspiracy:
                        relations[person1].append(person2)
                    else:
                        relations[person1].add(person2)
                        if person2 not in relations:
                            relations[person2] = set()
                        relations[person2].add(person1)
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{file_path}' n'a pas été trouvé.")
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier '{file_path}': {e}")
    return relations


def print_help():
    help_text = """USAGE
    ./game_of_graphs [--links fr p1 p2 | --plots fr cr n]

DESCRIPTION
    fr      file containing friendship relations between people
    pi      name of someone in the friendships file
    cr      file containing conspiracies intentions
    n       maximum length of friendship paths
"""
    print(help_text)

def bfs_shortest_path(graph, start, goal):
    if start not in graph or goal not in graph:
        return -1
    if start == goal:
        return 0
    visited = set()
    queue = [(start, 0)]
    while queue:
        current_node, depth = queue.pop(0)
        if current_node not in visited:
            visited.add(current_node)
            if current_node == goal:
                return depth
            for neighbor in graph[current_node]:
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))
    return -1

def bfs_all_distances(graph, start, n):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    queue = [start]

    while queue:
        current_node = queue.pop(0)
        for neighbor in graph[current_node]:
            if distances[current_node] + 1 < distances[neighbor]:
                distances[neighbor] = distances[current_node] + 1
                if distances[neighbor] <= n:
                    queue.append(neighbor)
    for node in distances:
        if distances[node] > n:
            distances[node] = 0
    return distances

def display_relationships(friendships, n):
    names = sorted(friendships.keys())
    print("Names:")
    print("\n".join(names))
    print("\nRelationships:")
    for name in names:
        distances = bfs_all_distances(friendships, name, n)
        print(" ".join(str(distances.get(other_name, -1)) for other_name in names))

def find_conspirators_against_cersei(conspiracies):
    conspirators = []
    for plotter, targets in conspiracies.items():
        if "Cersei Lannister" in targets:
            conspirators.append(plotter)
    return conspirators

def find_close_friend_conspirator(conspiracies, conspirators, distances, n):
    close_friends = [friend for friend, distance in distances.items() if distance <= n and distance > 0]
    close_friend_conspirators = {}

    for conspirator in conspirators:
        for close_friend in close_friends:
            if close_friend in conspiracies and conspirator in conspiracies[close_friend]:
                close_friend_conspirators[conspirator] = close_friend
    return close_friend_conspirators

def is_close_friend(person, distances, n):
    distance = distances.get(person, float('inf'))
    return 1 if distance <= n and distance > 0 else 0

def find_chain_to_protect_crown(conspiracies, conspirators, distances, n):
    chain_to_protect_crown = {}

    for conspirator in conspirators:
        allies = [plotter for plotter, targets in conspiracies.items() if conspirator in targets]
        for ally in allies:
            if distances.get(ally, float('inf')) <= n:
                plotters_against_ally = [plotter for plotter, targets in conspiracies.items() if ally in targets]
                close_friends_who_can_plot = {}
                plotter_ally = []
                for plotter in plotters_against_ally:
                    for close_friend, distance in distances.items():
                        if distance <= n and close_friend in conspiracies and plotter in conspiracies[close_friend]:
                            if is_close_friend(close_friend, distances, n) == 1:
                                close_friends_who_can_plot[plotter] = close_friend
                                plotter_ally = plotter
                if close_friends_who_can_plot:
                    chain_to_protect_crown[conspirator] = {
                        'ally': ally,
                        'ally_against_plotter': close_friends_who_can_plot[plotter],
                        'plotter_against_ally': plotter_ally
                    }
    return chain_to_protect_crown

def handle_plots(friendships, conspiracies, n):
    display_relationships(friendships, n)
    distances = bfs_all_distances(friendships, "Cersei Lannister", n)
    
    print("\nConspiracies:")
    conspirators = find_conspirators_against_cersei(conspiracies)
    close_friend_conspirators = find_close_friend_conspirator(conspiracies, conspirators, distances, n)
    if close_friend_conspirators:
        for conspirator, close_friend in close_friend_conspirators.items():
            print(f"{close_friend} -> {conspirator}")
            if conspirator in conspirators:
                conspirators.remove(conspirator)
    chain_to_protect_crown = find_chain_to_protect_crown(conspiracies, conspirators, distances, n)
    for conspirator, details in chain_to_protect_crown.items():
        print(f"{details['ally_against_plotter']} -> {details['plotter_against_ally']} -> {details['ally']} -> {conspirator}")
        if conspirator in conspirators:
                conspirators.remove(conspirator)
    if conspirators == []:
        print("\nResult:\nThe Crown is safe !")
    else:
        print("No conspiracy possible against", conspirators[0])
        print("\nResult:\nThere is only one way out: treason !")

def main():
    if len(sys.argv) < 2 or sys.argv[1] == '--help':
        print_help()
        return
    mode = sys.argv[1]
    if mode == "--links":
        if len(sys.argv) != 5:
            print("Usage: ./game_of_graphs --links fr_file person1 person2")
            return
        fr_file, person1, person2 = sys.argv[2], sys.argv[3], sys.argv[4]
        friendships = read_file(fr_file)
        degree = bfs_shortest_path(friendships, person1, person2)
        print(f"Degree of separation between {person1} and {person2}: {degree}")
    elif mode == "--plots":
        if len(sys.argv) != 5:
            print("Usage: ./game_of_graphs --plots fr_file cr_file n")
            return
        fr_file, cr_file, n = sys.argv[2], sys.argv[3], int(sys.argv[4])
        friendships = read_file(fr_file)
        conspiracies = read_file(cr_file, is_conspiracy=True)
        handle_plots(friendships, conspiracies, n)
    else:
        print("Mode inconnu. Utilisez --links ou --plots.")

if __name__ == "__main__":
    main()