import random
import os
import networkx as nx
import argparse  # <<<< CHANGE 1: Add this import


def calculate_num_vertices_from_tree(r, h):
    """
    Calculates the total number of vertices in a perfectly balanced r-ary tree of height h.
    Formula: (r^(h+1) - 1) / (r - 1) for r > 1, or h + 1 for r = 1.

    Args:
        r (int): The arity of the tree (number of children per node).
        h (int): The height of the tree (distance from root to furthest leaf).

    Returns:
        int: The total number of nodes in such a tree.
    """
    if r == 1:
        return h + 1
    return (r ** (h + 1) - 1) // (r - 1)


def generate_random_connected_graph_nx(scale, ef, min_weight, max_weight, seed):
    if scale < 0:
        raise ValueError("Tree height (h) must be non-negative.")
    if min_weight > max_weight:
        raise ValueError("min_weight cannot be greater than max_weight.")

    # 1. Create the perfectly balanced tree
    # The nodes are automatically labeled 0 to num_vertices - 1 by NetworkX.
    G = nx.fast_gnp_random_graph(2**scale, ef / (2**scale - 1), seed=seed)
    for u, v in G.edges():
        G[u][v]['weight'] = random.randint(0, 255)

    # The graph is guaranteed to be connected because it starts as a tree and only adds more edges.
    return G


def dijkstra_nx(graph, start_node):
    """
    Calculates the shortest path lengths from a specified start node to all
    other reachable nodes in the graph using NetworkX's built-in Dijkstra's algorithm.

    Args:
        graph (networkx.Graph): The graph for which to calculate shortest paths.
                                Edges are expected to have a 'weight' attribute.
        start_node (int): The node from which to start the shortest path calculation.

    Returns:
        dict: A dictionary where keys are nodes and values are their shortest
              distances from the start_node. If a node is unreachable, its value
              would be float('inf').
    """
    if start_node not in graph:
        raise ValueError(f"Start node {start_node} is not present in the graph.")

    # Use NetworkX's single_source_dijkstra_path_length function.
    # The 'weight' parameter tells Dijkstra to use the 'weight' attribute of edges.
    shortest_paths = nx.single_source_dijkstra_path_length(
        graph, source=start_node, weight="weight"
    )

    # Convert to a dictionary that includes all graph nodes.
    # For a connected graph, all nodes will have a finite path length.
    distances = {node: shortest_paths.get(node, float("inf")) for node in graph.nodes()}
    return distances


def distribute_graph_and_save(graph, num_vertices, num_processes, wzorcowa, output_dir):
    """
    Distributes the graph edges to K processes using a block distribution strategy
    and saves the relevant edges into separate input files for each process,
    following the specified format.

    Each process's file will contain:
    - First line: <total_vertices> <first_owned_vertex_index> <last_owned_vertex_index>
    - Subsequent lines: <u_node> <v_node> <weight> (for edges incident to owned nodes)

    Args:
        graph (networkx.Graph): The graph represented as a NetworkX Graph object.
        num_vertices (int): Total number of vertices in the graph.
        num_processes (int): The number of processes (K) to distribute the graph among.
        output_dir (str): The directory where the process-specific input files will be saved.
    """
    # Create the output directory if it doesn't already exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Calculate the base number of nodes assigned to each process
    nodes_per_process_base = num_vertices // num_processes

    current_node_start = 0
    for p_id in range(num_processes):
        # Determine the number of nodes for this specific process
        # Distribute remainder nodes (if any) to earlier processes
        num_nodes_for_this_process = nodes_per_process_base
        if p_id < (
            num_vertices % num_processes
        ):  # Check if this process gets an extra node
            num_nodes_for_this_process += 1

        # Calculate the actual start and end node indices for this process
        first_owned_vertex = current_node_start
        last_owned_vertex = current_node_start + num_nodes_for_this_process - 1

        owned_nodes = list(range(first_owned_vertex, last_owned_vertex + 1))
        najlepsze_dystanse = [wzorcowa[nod] for nod in owned_nodes]

        # Define the full path for the output file for this process
        output_filepath = os.path.join(output_dir, f"{p_id}.in")

        with open(output_filepath, "w") as f:
            # Write the first line: total_vertices first_owned_vertex last_owned_vertex
            f.write(f"{num_vertices} {first_owned_vertex} {last_owned_vertex}\n")

            # Iterate through all nodes owned by the current process
            for u in owned_nodes:
                # Iterate through all neighbors 'v' of 'u' and their edge data
                # graph.adj[u] is a dictionary where keys are neighbors and values are edge attributes
                if (
                    u in graph
                ):  # Ensure node 'u' actually exists and has neighbors in the graph
                    for v, data in graph[u].items():
                        weight = data["weight"]  # Get the weight of the edge (u, v)
                        # Write the edge in the format "u v weight" (no 'E' prefix)
                        # All edges incident to 'u' (where 'u' is an owned node) are included.
                        f.write(f"{u} {v} {weight}\n")

        with open(os.path.join(output_dir, f"{p_id}.out"), "w") as f:
            f.write("\n".join(map(str, najlepsze_dystanse)) + "\n")

        # Update the starting node for the next process
        current_node_start += num_nodes_for_this_process

    print(f"Generated input files for {num_processes} processes in '{output_dir}/'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate test inputs for distributed Dijkstra's algorithm."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed for the random number generator for reproducible results.",
    )
    parser.add_argument(
        "--height",
        type=int,
        required=True,
        help="Height (h) of the tree — distance from root to deepest leaf.",
    )
    parser.add_argument(
        "--num-procs",
        type=int,
        required=True,
        help="Number of processes for distributing the graph.",
    )
    parser.add_argument(
        "--edge-factor", type=int, default=2, help="Average number of edges per node."
    )

    parser.add_argument(
        "--skip-validation",
        action="store_false",
        dest="validation",
        help="Skip producing reference values by nx.Dijkstra.",
    )

    args = parser.parse_args()

    random.seed(args.seed)
    print(f"Random seed set to: {args.seed}")
    ef = args.edge_factor

    TREE_HEIGHT = args.height
    NUM_PROCESSES = args.num_procs
    VALIDATION = args.validation  # True unless --skip-validation is passed

    # Calculate the total number of vertices based on the tree parameters
    NUM_VERTICES = 2**TREE_HEIGHT
    TARGET_TOTAL_EDGES = int(NUM_VERTICES * ef)

    # Ensure NUM_VERTICES is at least 1 for small trees like (1,0) -> 1 node
    if NUM_VERTICES == 0:
        print("Calculated 0 vertices, adjusting to 1 for graph generation.")
        NUM_VERTICES = 1
        TREE_HEIGHT = 0  # Adjust height if arity 1 results in 0 nodes for a 0 height.
        # This edge case might not be strictly needed with current logic, but good for robustness.

    # Desired total number of edges in the graph.
    # Must be at least (NUM_VERTICES - 1) for connectivity.
    # A multiplier (e.g., 2.0 or 3.0) can be used to create denser graphs.
    # TARGET_TOTAL_EDGES = max(NUM_VERTICES - 1, int(NUM_VERTICES * 2.0))
    TARGET_TOTAL_EDGES = 16 * NUM_VERTICES
    if NUM_VERTICES == 1:  # A single node graph has 0 edges
        TARGET_TOTAL_EDGES = 0

    MIN_WEIGHT = 0  # Minimum integer weight for graph edges
    MAX_WEIGHT = 255  # Maximum integer weight for graph edges

    # --- Configuration Parameters for Distribution and Output ---
    ROOT_NODE = 0  # The source vertex for SSSP calculation (always 0)
    OUTPUT_DIRECTORY = f"random-scale{TREE_HEIGHT}-ef16-s{args.seed}_{NUM_VERTICES}_{NUM_PROCESSES}"  # Directory to save generated input files

    # Generate the random connected graph using NetworkX, starting with a balanced tree
    graph = generate_random_connected_graph_nx(TREE_HEIGHT, 16, MIN_WEIGHT, MAX_WEIGHT, args.seed)

    print(f"\n--- Running Serial Dijkstra's Algorithm for Verification ---")
    print(f"Calculating shortest paths from root node {ROOT_NODE} using NetworkX...")

    # Calculate shortest paths using NetworkX's Dijkstra
    shortest_paths_serial = (
        dijkstra_nx(graph, ROOT_NODE)
        if VALIDATION
        else {node: 0 for node in graph.nodes}
    )

    print(f"\nShortest path lengths from root node {ROOT_NODE} (serial Dijkstra):")
    # Print distances, sorted by node ID for readability
    for node, dist in sorted(shortest_paths_serial.items()):
        # If the graph is guaranteed connected, 'inf' should not appear for any node.
        # For single node graph, distance to itself is 0.
        if NUM_VERTICES == 1 and node == 0:
            print(f"  Node {node}: 0")

        if dist == float("inf"):
            print(
                f"  Node {node}: Unreachable (This indicates an issue with graph connectivity or root node)"
            )
            raise Exception()
    print("Serial Dijkstra calculation complete.")

    print(f"\n--- Distributing Graph Data for Distributed Processes ---")
    print(
        f"Distributing graph among {NUM_PROCESSES} processes, saving to '{OUTPUT_DIRECTORY}/'."
    )

    # Distribute the graph data and save to files in the new format
    distribute_graph_and_save(
        graph, NUM_VERTICES, NUM_PROCESSES, shortest_paths_serial, OUTPUT_DIRECTORY
    )

    print("\n--- Program Execution Complete ---")