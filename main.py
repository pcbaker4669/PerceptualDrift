import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import random

# Node class
class Node:
    def __init__(self, node_id, ideology_score, bias_multiplier):
        self.node_id = node_id
        self.ideology_score = ideology_score
        self.bias_multiplier = bias_multiplier  # Bias factor for this node

    def process_message(self, message_ideology, sensitivity):
        """
        Adjusts the message ideology based on this node's ideology score, bias, and message sensitivity.
        Non-linear drift is applied to amplify or dampen the effect of ideological differences.
        """
        delta = abs(self.ideology_score - message_ideology)
        drift = self.bias_multiplier * sensitivity * (delta ** 2)  # Quadratic effect
        if self.ideology_score > message_ideology:
            new_ideology = message_ideology + drift
        else:
            new_ideology = message_ideology - drift
            # Clamp ideology between 0 and 1
        return np.clip(new_ideology, 0, 1)

# Message class
class Message:
    def __init__(self, ideology_score):
        self.ideology_score = ideology_score

# Network class
class Network:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes = {}
        self.last_node_added = 0  # id's of the last node added

    def draw_graph(self):
        """
        Visualizes the graph using matplotlib.
        Node sizes are proportional to their ideology scores for clarity.
        Edge labels display message ideology scores.
        """
        pos = nx.spring_layout(self.graph)  # Positions for all nodes

        # Collect node colors based on their ideology scores
        node_colors = [self.nodes[node_id].ideology_score for node_id in self.graph.nodes]

        # Create a matplotlib figure and axis
        fig, ax = plt.subplots(figsize=(8, 6))

        # Draw nodes and edges
        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_size=500,
            node_color=node_colors,
            cmap=plt.cm.coolwarm,
            edge_color="gray",
            ax=ax,
        )

        # Add edge labels for message ideology scores
        edge_labels = {
            (u, v): f"{d['message_ideology']:.2f}"
            for u, v, d in self.graph.edges(data=True)
            if "message_ideology" in d
        }
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, ax=ax)

        # Add a colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.coolwarm)
        sm.set_array(node_colors)
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label("Ideology Score")

        # Add a title
        ax.set_title("Network Visualization with Message Ideology Scores")
        plt.show()

    def add_node(self, node_id, bias_multiplier=1.0):
        """
        Adds a node to the graph and stores the Node object.
        Automatically connects the new node to the last added node if applicable.
        """
        ideology_score = random.random()  # Random ideology
        node = Node(node_id, ideology_score, bias_multiplier)
        self.nodes[node_id] = node  # Store the Node object
        self.graph.add_node(node_id, ideology_score=ideology_score, bias_multiplier=bias_multiplier)

        # Automatically connect the new node to the previous node
        if node_id > 0:  # Skip connecting the first node
            self.graph.add_edge(self.last_node_added, node_id)

        # Update the last node tracker
        self.last_node_added = node_id

    def add_edge(self, source_id, target_id):
        """
        Adds a directed edge between two nodes in the graph.
        """
        self.graph.add_edge(source_id, target_id)

    def add_edge_from_last_node(self, target_id):
        """
        Adds a directed edge from the last added node to the target node.
        """
        source_id = self.last_node_added
        self.graph.add_edge(source_id, target_id)

    def propagate_message(self, run_id, source_id, target_id, sensitivity=1.0):
        """
        Simulates message propagation from source to target, adjusting ideology along the path.
        Stores updated message ideology scores as edge attributes.
        """
        path = nx.shortest_path(self.graph, source=source_id, target=target_id)
        # print(f"Path: {path}")

        message = Message(self.nodes[source_id].ideology_score)
        # print(f"Initial message ideology: {message.ideology_score}")

        # Prepare CSV header
        path_length = len(path)
        # Pass the message through each node in the path
        for i in range(len(path) - 1):
            current_node_id = path[i]
            next_node_id = path[i + 1]

            current_node = self.nodes[current_node_id]
            before_score = message.ideology_score
            message.ideology_score = current_node.process_message(before_score, sensitivity)

            # Store the updated message ideology score as an edge attribute
            self.graph.edges[current_node_id, next_node_id]["message_ideology"] = message.ideology_score

            print(f"{run_id}", f"{current_node_id}, {path_length}, {current_node.ideology_score:.5f}, "
                  f"{sensitivity}, "
                  f"{current_node.bias_multiplier:.2f}, "
                  f"{message.ideology_score:.3f}")

        # print(f"Final message ideology at target {target_id}: {message.ideology_score:.3f}")

network_chain = [3, 5, 7, 10]
sensitivity = [.5, 1.0, 1.5, 2.0 ]
# Example Usage

if __name__ == "__main__":
  #   # Create a simple chain network
  #   network = Network()
  #
  #   # Add nodes with varying bias multipliers
  #   network.add_node(0, bias_multiplier=1.0)  # Source node
  #   message_hops = 4
  #
  #   # Add intermediate nodes
  #   for i in range(1, message_hops):
  #       network.add_node(i, bias_multiplier=random.uniform(0.5, 2.0))  # Intermediate nodes with random bias
  #
  #   # Add target node
  #   network.add_node(message_hops, bias_multiplier=1.5)  # Target node
  #
  #   # Propagate a message with a specific sensitivity
  #   network.propagate_message(0, message_hops, sensitivity=1.2)
  #
  # # Visualize the network
  #   network.draw_graph()
  print("Run ID, Node ID, Path Length, Node Ideology, Sensitivity, Bias_Multiplier, Message_Ideology_Score")
  run_id = 0
  for num_nodes in network_chain:
      for s in sensitivity:
          network = Network()
          for node_id in range(num_nodes):
              network.add_node(node_id, bias_multiplier=random.uniform(0.5, 3.0))
          network.propagate_message(run_id, 0, num_nodes - 1, sensitivity=s)
          run_id += 1
