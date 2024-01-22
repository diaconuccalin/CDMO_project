import os
import subprocess
import sys
import time

from src.io_utils import write_to_json


def run_instance(data_path):
    # Start timer
    time_started = time.time()

    # Open process
    p = subprocess.Popen(
        [
            'minizinc',
            '--solver', 'chuffed',
            os.path.join('.', "src", "CP", "the_problem.mzn"),
            data_path,
            "--time-limit", "290000",
            "--random-seed", "42"
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for execution to finish and get output
    output, _ = p.communicate()

    # Stop timer
    time_delta = time.time() - time_started

    # Extract the number of couriers
    with open(data_path, "r") as f:
        content = f.readlines()
    courier_number = int(content[0][4:-2])

    return output, time_delta, courier_number


def main():
    """
    The main function.

    :return: None
    """

    the_dir = os.path.join('.', "data", "CP", "problem_instances")

    instance_number = int(sys.argv[1])
    experiment_name = sys.argv[2]

    if instance_number == 0:
        for el in os.listdir(the_dir):
            print("Working on ", el)
            data_path = os.path.join(the_dir, el)
            output, time_delta, courier_number = run_instance(data_path)
            inst_n = el[-6:-3]
            write_to_json(output, inst_n, experiment_name, time_delta, courier_number)
    else:
        print("Working on instance ", instance_number)
        data_path = os.path.join(the_dir, "inst%02d.dzn" % (instance_number, ))
        output, time_delta, courier_number = run_instance(data_path)
        write_to_json(output, instance_number, experiment_name, time_delta, courier_number)

    return None


if __name__ == "__main__":
    main()
