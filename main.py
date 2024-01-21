import os
import subprocess
import sys
import time

from src.io_stream import write_to_json


def run_instance(data_path):
    p = subprocess.Popen(
        ['minizinc', '--solver', 'gecode', './res/CP/the_problem.mzn', data_path, "--time-limit", "20000"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    time_started = time.time()
    output, _ = p.communicate()
    time_delta = time.time() - time_started

    return output, time_delta


def main():
    """
    The main function.

    :return: None
    """

    the_dir = "./data/CP/problem_instances"

    max_report = 0
    for el_2 in os.listdir("reports"):
        el_2 = int(el_2[6:])
        if el_2 > max_report:
            max_report = el_2

    instance_number = int(sys.argv[1])

    if instance_number == 0:
        for el in os.listdir(the_dir):
            print("Working on ", el)
            data_path = os.path.join(the_dir, el)
            output, time_delta = run_instance(data_path)
            inst_n = el[-6:-3]
            write_to_json(output, inst_n, str(max_report + 1), time_delta)
    else:
        print("Working on instance ", instance_number)
        data_path = os.path.join(the_dir, "inst%02d.dzn" % (instance_number, ))
        output, time_delta = run_instance(data_path)
        write_to_json(output, instance_number, str(max_report + 1), time_delta)

    return None


if __name__ == "__main__":
    main()
