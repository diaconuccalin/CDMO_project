import os

from src.io_stream import read_input_file, create_dzn


def main():
    """
    The main function.

    :return: None
    """

    for el in os.listdir("data/problem_instances"):
        if el.endswith(".dat"):
            problem = read_input_file("data/problem_instances/" + el)
            create_dzn(problem, "data/CP/problem_instances/" + el[:-4] + ".dzn")

            print((problem.distances == problem.distances.T).all())
            print(len(problem.max_loads) != len(set(problem.max_loads)))
            print(len(problem.sizes) != len(set(problem.sizes)))
            print()

    return None


if __name__ == "__main__":
    main()
