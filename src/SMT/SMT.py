from z3 import *
import os
from timeit import default_timer as timer
import time
import math
import json


def import_data(path):
    with open(path, 'r') as f:
      lines = [line.strip() for line in f]

      # Assign the first line to the m variable (Couriers)
      m = int(lines[0])

      # Assign the second line to the n variable (Locations)
      n = int(lines[1])

      # Assign the third line to the li variable (Couriers' maximum load)
      li = [int(x) for x in lines[2].split()]

      # Assign the fourth line to the sj variable (Load sizes)
      sj = [int(x) for x in lines[3].split()]

      # Assign the remaining lines to the Di_j variable (Distances between locations)
      Di_j = []
      for line in lines[4:]:
        Di_j.append([int(x) for x in line.split()])

    return m, n, li, sj, Di_j


def solve_sat(m, n, Di_j, sj, li):

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PRELIMINARIES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    result_dict = dict()

    # Initialize default result values
    result_dict["time"] = -1
    result_dict["optimal"] = False
    result_dict["obj"] = None
    result_dict["sol"] = None

    s = Optimize()

    # Start timer
    start_time = timer()
    elapsed_time = -1


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ VARIABLES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Binary variable, if x = 1, then courier i has moved from location j to location k (includes origin)
    x = {}
    for i in range(m):
        for j in range(n + 1):
            for k in range(n + 1):
                x[i, j, k] = Bool(f'x_{i}_{j}_{k}')


    # Binary variable, if y = 1, then courier i has visited location j
    y = {}
    for i in range(m):
        for j in range(n):
            y[i, j] = Bool(f'y_{i}_{j}')

    # Integer MTZ variable
    u = {}
    for i in range(m):
        for j in range(n+1):
            u[i, j] = Int(f'u_{i}_{j}')

    # Initialize variable to be used in the objective function
    max_distance = Int('max_distance')

    if check_timeout(start_time):
      return result_dict


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTRAINTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Objective function is defined here, minimizes the maximum distance that any one courier has to travel
    constraints = []
    for i in range(m):
        constraints.append(Sum([x[i, j, k] * Di_j[j][k] for j in range(n+1) for k in range(n+1)]) <= max_distance)

    # Add constraints
    for constraint in constraints:
        s.add(constraint)



    # Assignment constraints only exactly one visit per location
    assign_constraints = [Sum([If(y[i,j], 1, 0) for i in range(m)]) == 1 for j in range(n)]
    s.add(assign_constraints)

    if check_timeout(start_time):
      return result_dict

    # Linking constraint, limits a courier to a single y variable per location it arrives to or departs from
    courier_tour_depart_constraints = [
        Sum([If(x[i,j,k], 1, 0) for k in range(n + 1) if j != k]) == If(y[i,j], 1, 0) for j in range(n)
        for i in range(m)
    ]
    s.add(courier_tour_depart_constraints)

    if check_timeout(start_time):
      return result_dict


    courier_tour_arrive_constraints = [
        Sum([If(x[i,j,k], 1, 0) for j in range(n + 1) if j != k]) == If(y[i,k], 1, 0) for k in range(n)
        for i in range(m)
    ]
    s.add(courier_tour_arrive_constraints)

    if check_timeout(start_time):
      return result_dict


    # Load capacity constraint (for number of couriers)
    load_capacity_constraints = [
        Sum([sj[j] * If(y[i,j], 1, 0) for j in range(n)]) <= li[i] for i in range(m)
    ]
    s.add(load_capacity_constraints)

    if check_timeout(start_time):
      return result_dict


    # MTZ subtour elimination constraint
    for i in range(m):
        for j in range(n+1):
            for k in range(n+1):
                if j != n and j != k:
                    s.add(u[i,j] - u[i,k] + n * If(x[i,j,k], 1, 0) <= n - 1)

    if check_timeout(start_time):
      return result_dict

    # Ensure for each courier that they leave origin and come back to it exactly once
    courier_flow_start_constraints = [
        Sum([If(x[i,n,k], 1, 0) for k in range(n + 1)]) == 1 for i in range(m)
    ]
    s.add(courier_flow_start_constraints)

    courier_flow_end_constraints = [
        Sum([If(x[i,j,n], 1, 0) for j in range(n + 1)]) == 1 for i in range(m)
    ]
    s.add(courier_flow_end_constraints)


    # Set objective
    s.minimize(max_distance)


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ SOLVING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Sets time limit for solver
    s.set("timeout", 300000)
    print("SOLVING...")
    start_time = timer()

    # Solve
    is_sat = s.check()

    end_time = timer()
    elapsed_time = end_time-start_time

    # Saving unordered routes travelled into a list
    routes = []
    for i in range(m):
        route = []
        for j in range(n + 1):
            for k in range(n + 1):
                if s.model()[x[i, j, k]]:
                    route.append((j+1, k+1))
        routes.append(route)

    # Assign result to dictionary if model finds optimal solution
    if is_sat == sat:
        result_dict["time"] = elapsed_time
        result_dict["optimal"] = True
        result_dict["obj"] = s.model()[max_distance].as_long()
        result_dict["paths"] = routes

    # Assign best found results to dictionary if model does not find optimal solution
    else:
        result_dict["time"] = 300
        result_dict["optimal"] = False
        try:
            if s.model()[max_distance].as_long():
                result_dict["obj"] = s.model()[max_distance].as_long()
                result_dict["paths"] = routes

        # Does not assign results to dictionary of no solution found (even non-optimal)
        except AttributeError:
            return result_dict

    return result_dict


def check_timeout(start_time):
    constraint_adding_timeout = 180000
    # Check that constraints are added within timeout restriction
    if (timer() - start_time) > (constraint_adding_timeout / 1000):
      return True
    else:
      return False


def order_routes(route_list):
    ordered_routes = []
    first_transfer = max(route_list, key=lambda x: x[0])
    # Remove the first_transfer from the original list
    route_list.remove(first_transfer)
    # Set first_transfer as first instance of the list
    route_list.insert(0, first_transfer)

    while route_list:
        for i, route in enumerate(route_list):
            # Checks that final destination and starting destination are the same
            if not ordered_routes or route[0] == ordered_routes[-1][1]:
                ordered_routes.append(route)
                del route_list[i]
                break
    return ordered_routes


def main_smt(instance):
    m, n, li, sj, Di_j = import_data("Instances/inst{0}.dat".format(instance))

    # Solve instance
    result_dict = solve_sat(
        m=m,
        n=n,
        sj=sj,
        Di_j=Di_j,
        li=li
    )

    paths = []
    if "paths" in result_dict:
        for route in result_dict["paths"]:
            ordered_destinations = order_routes(route)
            path = []
            for r in ordered_destinations[:-1]:
                path.append(r[1])
            paths.append(path)

    # Prepare directories if they don't exist yet
    if not os.path.exists("res"):
        os.mkdir("res")
    if not os.path.exists(os.path.join("res", "SMT")):
        os.mkdir(os.path.join("res", "SMT"))

    # Prepare json path
    json_file_path = os.path.join("res", "SMT", instance + ".json")

    # Read existing data from the json
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as f:
            loaded_data = json.load(f)
    else:
        loaded_data = dict()

    experiment_name = "SMT"
    data = {
        experiment_name: {
            "time": int(math.floor(result_dict['time'])),
            "optimal": result_dict['optimal'],
            "obj": int(result_dict['obj']) if result_dict['obj'] else None,
            "sol": paths
        }
    }

    for key in data.keys():
        loaded_data[key] = data[key]

    # Creates JSON file with associated data
    with open(json_file_path, "w") as json_file:
        json.dump(loaded_data, json_file, indent=4)
