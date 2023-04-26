import sys

from src.io_stream import read_input_file


def main():
    """
    The main function. Required arguments:
    - string representing the path to the input file, given in the standard format; the path must be relative to the\
      root of the project
    :return: None
    """
    problem = read_input_file(sys.argv[1])

    return None


if __name__ == "__main__":
    main()
