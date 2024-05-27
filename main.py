import os
import subprocess
import sys
import time

from math import floor

from src.SAT.sat_model import solve_sat
from src.io_utils import write_to_json, output_to_dict_cp, read_input_file
from src.MIP.main_mip import main_mip


def run_cp_instance(data_path):
    # Start timer
    time_started = time.time()

    # Open process
    p = subprocess.Popen(
        [
            'minizinc',
            '--solver', 'gecode',
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


def run_sat_instance(
        data_path,
        ignore_max_load_symmetry_breaking_constraints=True,
        ignore_distance_symmetry_breaking_constraints=True,
        constraint_adding_timeout=600000,
        solving_timeout=300000
):
    # Read problem data from file
    instance = read_input_file(data_path)

    # Solve instance
    result, instance_obj = solve_sat(
        instance,
        ignore_max_load_symmetry_breaking_constraints=ignore_max_load_symmetry_breaking_constraints,
        ignore_distance_symmetry_breaking_constraints=ignore_distance_symmetry_breaking_constraints,
        constraint_adding_timeout=constraint_adding_timeout,
        solving_timeout=solving_timeout
    )

    # Extract solution
    if len(result.keys()) == 1:
        return None
    else:
        item_assignment = result["item_assignment"]
        pre_table = result["pre_table"]
        max_dist = result["max_dist"]

    elapsed_time = floor(result["elapsed_time"] / 1000)

    # Prepare output variables (solution will contain the routes)
    solution = list()

    # Find item assignments and routes
    for idx, co_assignment in enumerate(item_assignment):
        # Get all items for current courier
        items = [i for i, val in enumerate(co_assignment) if val]

        # Case when courier delivers no items
        if len(items) == 0:
            solution.append(list())
            continue

        # Prepare to extract route
        current_pre_col = None

        for item in items:
            # Find first item delivered by courier and initialize route
            if not any(pre_table[item]):
                current_item = item
                solution.append([item + 1])
                current_pre_col = [row[current_item] for row in pre_table]
                break

        # Go through route while successor exists
        while any(current_pre_col):
            current_item = current_pre_col.index(True)
            current_pre_col = [row[current_item] for row in pre_table]
            solution[idx].append(current_item + 1)

    # Prepare output dict
    if elapsed_time >= (solving_timeout / 1000):
        output_dict = {
            "time": 300,
            "optimal": False,
            "obj": max_dist,
            "sol": solution
        }
    else:
        output_dict = {
            "time": elapsed_time,
            "optimal": True,
            "obj": max_dist,
            "sol": solution
        }

    return output_dict


def main():
    """
    The main function.

    :return: None
    """

    the_dir = os.path.join('.', "data", "problem_instances")

    instance_number = int(sys.argv[1])
    experiment_name = sys.argv[2]
    method_name = sys.argv[3]

    if method_name == "CP":
        the_dir = os.path.join('.', "data", "CP", "problem_instances")

        if instance_number == 0:
            for el in os.listdir(the_dir):
                print("Working on ", el)
                data_path = os.path.join(the_dir, el)
                output, time_delta, courier_number = run_cp_instance(data_path)
                parsed_output = output_to_dict_cp(output, experiment_name, time, courier_number)
                inst_n = el[-6:-3]
                write_to_json(parsed_output, inst_n, method_name)
        else:
            print("Working on instance ", instance_number)
            data_path = os.path.join(the_dir, "inst%02d.dzn" % (instance_number, ))
            output, time_delta, courier_number = run_cp_instance(data_path)
            parsed_output = output_to_dict_cp(output, experiment_name, time, courier_number)
            write_to_json(parsed_output, instance_number, method_name)

    if method_name == "SAT":
        if instance_number == 0:
            for el in os.listdir(the_dir):
                print("Working on ", el)
                sat_solution = dict()
                data_path = os.path.join(the_dir, el)
                solution = run_sat_instance(data_path)
                if solution is not None:
                    sat_solution[experiment_name] = solution
                    inst_n = el[-6:-3]
                    write_to_json(sat_solution, inst_n, method_name)
        else:
            print("Working on instance ", instance_number)
            sat_solution = dict()
            data_path = os.path.join(the_dir, "inst%02d.dat" % (instance_number, ))
            solution = run_sat_instance(data_path)
            if solution is not None:
                sat_solution[experiment_name] = solution
                write_to_json(sat_solution, instance_number, method_name)

    if method_name == "MIP":
        if instance_number == 0:
            for i in range(1, 22):
                print("Working on instance ", i)
                main_mip(i)
        else:
            print("Working on instance ", instance_number)
            main_mip(instance_number)

    return None


if __name__ == "__main__":
    main()
