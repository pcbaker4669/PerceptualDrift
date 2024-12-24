import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import random

random.seed(1234)

from networkx.classes import number_of_nodes


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
        pos = nx.shell_layout(self.graph)

        # Collect node colors based on their ideology scores
        node_colors = [self.nodes[node_id].ideology_score for node_id in self.graph.nodes]

        # Create a matplotlib figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Draw nodes and edges
        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_size=300,
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


        # Turn off axis ticks and labels for a cleaner look
        ax.axis("off")
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
        # use initial_message_ideology to compare change in message
        initial_message_ideology = message.ideology_score
        fidelity_drift = 0  # cumulative add of abs(drift), how much change
        plausibility_drift = 0 # cumulative add of drift, if hits endpoints, we don't believe it
        fail_flag = False  # the message became implausible and did not achieve target
        # Prepare CSV header
        path_length = len(path)
        # Pass the message through each node in the path
        for i in range(path_length - 1):
            current_node_id = path[i]
            next_node_id = path[i + 1]

            current_node = self.nodes[current_node_id]
            before_score = message.ideology_score
            message.ideology_score = current_node.process_message(before_score, sensitivity)

            if message.ideology_score == 0 or message.ideology_score == 1:
                fail_flag = True

            # Store the updated message ideology score as an edge attribute
            self.graph.edges[current_node_id, next_node_id]["message_ideology"] = message.ideology_score

            # leave off the starter node from the output
            if i != 0:
                node_drift = message.ideology_score - before_score
                fidelity_drift += abs(node_drift)
                plausibility_drift += node_drift

                print(f"{run_id}, {current_node_id}, "
                      f"{path_length}, "
                      f"{initial_message_ideology:.5f}, "
                      f"{current_node.ideology_score:.5f}, "
                      f"{sensitivity}, "
                      f"{current_node.bias_multiplier:.2f}, "
                      f"{before_score:.5f}, "
                      f"{message.ideology_score:.5f}, "
                      f"{fidelity_drift:.5f}, "
                      f"{plausibility_drift:.5}, {not fail_flag}")
            if fail_flag:  # plausibility_drift hit and endpoint
                break
        # print(f"Final message ideology at target {target_id}: {message.ideology_score:.3f}")

num_nodes_in_chain = 10
bias_range = [(0.5, 1.0), (0.5, 2.0), (0.5, 3.0)]
sensitivity = [.5, 1.0, 1.5, 2.0 ]
# Example Usage

if __name__ == "__main__":
  print("Run ID, Node ID, Path Length, Initial Msg Ideology, Node Ideology, "
        "Sensitivity, Bias_Multiplier, Init Msg Ideo Score, Msg Ideo Score, "
        "fidelity_drift, plausibility_drift, Transmission Success")
  run_id = 0
  for bias in bias_range:
      for s in sensitivity:
          for j in range(10):
              network = Network()
              for node_id in range(num_nodes_in_chain):
                  network.add_node(node_id, bias_multiplier=random.uniform(bias[0], bias[1]))
              network.propagate_message(run_id, 0, num_nodes_in_chain - 1, sensitivity=s)
              run_id += 1
              # Visualize the network
              # network.draw_graph()