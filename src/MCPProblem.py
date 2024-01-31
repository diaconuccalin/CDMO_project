class MCPProblem:
    """
    Class to store the parameters of an MCP problem.
    """
    def __init__(self, n_couriers, n_items, max_loads, sizes, distances):
        """
        Create an instance of an MCP problem, having all required parameters
        :param n_couriers: int - number of couriers (m)
        :param n_items: int - number of items (n)
        :param max_loads: list(int) - list containing the maximum load size of each courier (l_i)
        :param sizes: list(int) - list containing the size of each item (s_j)
        :param distances: ndarray - array containing the distances between each two delivery points (D_i_j)
        """
        self.n_couriers = n_couriers
        self.n_items = n_items
        self.max_loads = max_loads
        self.sizes = sizes
        self.distances = distances
