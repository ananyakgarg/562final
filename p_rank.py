import numpy as np

def get_degree_matrix(adj_matrix):
    """ Generates a degree matrix from an adjacency matrix. """
    return [[adj_matrix[i].sum() if i == j else 0 for j in range(len(adj_matrix))] for i in range(len(adj_matrix))]

def find_inverse_of_degree_matrix(degree_matrix):
    """ Finds the inverse of the degree matrix, handling zero entries safely. """
    return [[1 / degree_matrix[i][j] if degree_matrix[i][j] != 0 else 0 for j in range(len(degree_matrix))] for i in range(len(degree_matrix))]

def get_transition_matrix(adj_matrix):
    """ Computes the transition matrix from the adjacency matrix. """
    degree_matrix = get_degree_matrix(adj_matrix)
    inverse_degree_matrix = find_inverse_of_degree_matrix(degree_matrix)
    return np.dot(np.array(inverse_degree_matrix), adj_matrix).T

def page_rank(adj_matrix, power=2 ** 30):
    """ Calculates the PageRank of nodes in a graph represented by an adjacency matrix. """
    transition_matrix = get_transition_matrix(adj_matrix)
    transition_matrix = np.linalg.matrix_power(transition_matrix, power)

    initial_probabilities = np.array([1 / len(adj_matrix) for _ in range(len(adj_matrix))]).reshape((len(adj_matrix), 1))
    return np.dot(transition_matrix, initial_probabilities)

# Usage of functions in an example
if __name__ == "__main__":
    # Example adjacency matrix
    adj_matrix = np.array([
        [0, 1, 0, 0],
        [0, 0, 1, 1],
        [1, 0, 0, 0],
        [0, 0, 1, 0]
    ])
    result = page_rank(adj_matrix)
    print("PageRank Results:", result)
