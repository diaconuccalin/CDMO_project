# Importing all necessary libraries
import json
import math
import os

import gurobipy as gp

from gurobipy import GRB
from timeit import default_timer as timer


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


def nearest_neighbor_heuristic(Di_j, m, n, sj, li):
    routes = []
    unvisited_locations = set(range(n))
    max_distances = [0] * m
    current_load = [0] * m

    for i in range(m):
        # Sets depot as starting location
        start = [n]
        routes.append(start)

    while unvisited_locations:
        nearest_neighbors = {}
        for i in range(m):
            current_location = routes[i][-1]
            feasible_neighbors = [j for j in unvisited_locations if current_load[i] + sj[j] <= li[i]]

            if not feasible_neighbors:
                continue  # Skip to the next courier if no feasible neighbors

            # Finds next location that minimizes distance travelled by courier i
            best_customer = min(feasible_neighbors, key=lambda j: max_distances[i] + Di_j[current_location][j])
            nearest_neighbors[i] = best_customer

        if not nearest_neighbors:
            break  # Break the loop if no feasible neighbors for any courier

        # Finds next location that minimizes the maximum distance travelled by any courier
        closest_courier = min(
            nearest_neighbors.keys(),
            key=lambda j: Di_j[routes[j][-1]][nearest_neighbors[j]] + max_distances[j])

        # Update the current demand for the selected courier
        current_load[closest_courier] += sj[nearest_neighbors[closest_courier]]

        max_distances[closest_courier] += Di_j[routes[closest_courier][-1]][nearest_neighbors[closest_courier]]

        routes[closest_courier].append(nearest_neighbors[closest_courier])
        # Removes the nearest neighbor from list of available locations
        unvisited_locations.remove(nearest_neighbors[closest_courier])

    # Return to the depot
    [route.append(n) for route in routes]
    return routes


def initialize_routes(initial_routes, m, x):
    routes = [list(zip(location[:-1], location[1:])) for location in initial_routes]
    for i in range(m):
        for movement in routes[i]:
            x[i, movement[0], movement[1]].start = 1


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


def main_mip(instance):
    # Setting Parameters to access Gurobi environment
    params = {
        "WLSACCESSID": 'a8ff319c-dbbd-4eb8-8e06-0aba81176e45',
        "WLSSECRET": '318dbc76-0352-4577-93dc-b5a881ede973',
        "LICENSEID": 2467001,
    }
    env = gp.Env(params=params)

    # Create the model within the Gurobi environment
    model = gp.Model(env=env)

    m, n, li, sj, Di_j = import_data("data/problem_instances/inst%02d.dat" % (instance, ))

    start_time = timer()

    # Sets time limit
    model.setParam("TimeLimit", 285)

    # Binary variable, if x = 1, then courier i has moved from location j to location k (includes origin)
    x = {}
    for i in range(m):
        for j in range(n + 1):
            for k in range(n + 1):
                x[i, j, k] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}_{k}")

    # Turn on/off whether the model uses a heuristic based warm start
    heuristic = True
    if heuristic:
        # Warm starts initial solution using nearest neighbor heuristic
        initial_routes = nearest_neighbor_heuristic(Di_j, m, n, sj, li)
        # Sets x[i, j, k] = 1 start values according to initial routes found using the NN heuristic
        initialize_routes(initial_routes, m, x)

    # Binary variable, if y = 1, then courier i has visited location j
    y = {}
    for i in range(m):
        for j in range(n):
            y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    # Integer MTZ variable
    u = {}
    for i in range(m):
        for j in range(n + 1):
            u[i, j] = model.addVar(vtype=GRB.INTEGER)

    # Initialize variable to be used in the objective function
    max_distance = model.addVar(vtype=GRB.INTEGER)

    # Objective function is defined here, minimizes the maximum distance that any one courier has to travel
    for i in range(m):
        model.addConstr(
            gp.quicksum(x[i, j, k] * Di_j[j][k] for j in range(n + 1) for k in range(n + 1)) <= max_distance)

    model.setObjective(max_distance, GRB.MINIMIZE)

    # Assignment constraints only exactly one visit per location
    for j in range(n):
        model.addConstr(gp.quicksum(y[i, j] for i in range(m)) == 1, f"assign_location_{j}")

    # Linking constraint, limits a courier to a single y variable per location it arrives to or departs from
    for i in range(m):
        for j in range(n):
            model.addConstr(gp.quicksum(x[i, j, k] for k in range(n + 1) if j != k) == y[i, j], f"courier_tour_{i}_{j}")

    for i in range(m):
        for k in range(n):
            model.addConstr(gp.quicksum(x[i, j, k] for j in range(n + 1) if j != k) == y[i, k], f"courier_tour_{i}_{k}")

    # Load capacity constraint (for number of couriers)
    for i in range(m):
        model.addConstr(gp.quicksum(sj[j] * y[i, j] for j in range(n)) <= li[i], f"courier_capacity_{i}")

    # MTZ constraint
    for i in range(m):
        for j in range(n + 1):
            for k in range(n + 1):
                if j != n and j != k:
                    model.addConstr(u[i, j] - u[i, k] + n * x[i, j, k] <= n - 1)

    # Ensure for each courier that they leave origin and come back to it exactly once
    for i in range(m):
        model.addConstr(gp.quicksum(x[i, n, k] for k in range(n + 1)) == 1, name=f'courier_flow_start_{i}')

    for i in range(m):
        model.addConstr(gp.quicksum(x[i, j, n] for j in range(n + 1)) == 1, name=f'courier_flow_end_{i}')

    # Flow constraint, each courier must visit a location and then move to visit another location
    for i in range(m):
        for j in range(n):
            model.addConstr(gp.quicksum(x[i, j, k] for k in range(n)) - gp.quicksum(x[i, j, k] for k in range(n)) == 0,
                            name=f'flow_conservation_{i}_{j}')

    model.optimize()

    end_time = timer()

    time = end_time - start_time

    # Print the solution and prepares data for the JSON file
    if model.status == GRB.OPTIMAL:
        is_optimal = True
        routes = []
        print("\nOptimal solution found:")
        for i in range(m):
            route = []
            for j in range(n + 1):
                for k in range(n + 1):
                    if x[i, j, k].x > 0.5:
                        route.append((j + 1, k + 1))
            print(f"Courier {i + 1}: {route}")
            routes.append(route)
        print("\nTotal distance:", model.objVal)
        result = model.objVal
    else:
        is_optimal = False
        time = 300
        result = 0
        routes = []
        if model.objVal <= 10000:
            for i in range(m):
                route = []
                for j in range(n + 1):
                    for k in range(n + 1):
                        if x[i, j, k].x > 0.5:
                            route.append((j + 1, k + 1))
                print(f"Courier {i + 1}: {route}")
                routes.append(route)
            result = model.objVal
        print("No solution found.")

    paths = []
    for route in routes:
        ordered_destinations = order_routes(route)
        path = []
        for r in ordered_destinations[:-1]:
            path.append(r[1])
        paths.append(path)

    # Prepare directories if they don't exist yet
    if not os.path.exists("res"):
        os.mkdir("res")
    if not os.path.exists(os.path.join("res", "MIP")):
        os.mkdir(os.path.join("res", "MIP"))

    # Prepare json path
    json_file_path = os.path.join("res", "MIP", "%02d" % (instance, ) + ".json")

    # Read existing data from the json
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as f:
            loaded_data = json.load(f)
    else:
        loaded_data = dict()

    experiment_name = "Heuristic" if heuristic else "No Heuristic"
    data = {
        experiment_name: {
            "time": int(math.floor(time)),
            "optimal": True if is_optimal else False,
            "obj": int(result),
            "sol": paths
        }
    }

    for key in data.keys():
        loaded_data[key] = data[key]

    # Creates JSON file with associated data
    with open(json_file_path, "w") as json_file:
        json.dump(loaded_data, json_file, indent=4)
