import numpy as np

from src.MCPProblem import MCPProblem


def read_input_file(file_path):
    """
    Function to read information from a file given in the official format.

    :param file_path: str - path to the input file, relative to the project root
    :return: MCPProblem object, containing the information read from the file
    """
    # Read file
    with open(file_path) as fin:
        content = fin.readlines()

    # Parse file
    n_couriers = int(content[0][:-1])
    n_items = int(content[1][:-1])

    max_loads = list()
    for max_load in content[2][:-1].split():
        max_loads.append(int(max_load))

    sizes = list()
    for size in content[3][:-1].split():
        sizes.append(int(size))

    distances = np.zeros([n_items + 1, n_items + 1])
    for i in range(n_items + 1):
        distances_row = content[4 + i][:-1].split()
        for j in range(n_items + 1):
            distances[i][j] = int(distances_row[j])

    return MCPProblem(n_couriers, n_items, max_loads, sizes, distances)
