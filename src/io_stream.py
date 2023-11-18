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

    distances = np.zeros([n_items + 1, n_items + 1], dtype=int)
    for i in range(n_items + 1):
        distances_row = content[4 + i][:-1].split()
        for j in range(n_items + 1):
            distances[i][j] = int(distances_row[j])

    return MCPProblem(n_couriers, n_items, max_loads, sizes, distances)


def create_dzn(problem, file_path):
    """
    Create dzn file for CP problems, based on problem object

    :param problem: MCPProblem - object containing the data of the problem
    :param file_path: str - path to the output file, relative to the project root
    :return: None
    """

    with open(file_path, 'a') as f:
        f.write("m = " + str(problem.n_couriers) + ";\n")
        f.write("n = " + str(problem.n_items) + ";\n")
        f.write("\n")
        f.write("l = " + str(problem.max_loads) + ";\n")
        f.write("s = " + str(problem.sizes) + ";\n")
        f.write("\n")
        for i in range(problem.n_items + 1):
            list_to_print = "|"
            for j in range(problem.n_items + 1):
                list_to_print += (str(problem.distances[i, j]) + ", ")

            list_to_print = list_to_print[:-2]

            if i == 0:
                f.write("D = [" + list_to_print + "\n")
            elif i == problem.n_items:
                f.write("     " + list_to_print + "|];\n")
            else:
                f.write("     " + list_to_print + "\n")

    return None
