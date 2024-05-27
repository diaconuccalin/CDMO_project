from solve_utils import *
import time

from src.SAT.math_utils import *
from src.SAT.solve_utils import *

from z3 import *


def solve_sat(
        instance,
        exactly_one=exactly_one_seq,
        ignore_max_load_symmetry_breaking_constraints=True,
        ignore_distance_symmetry_breaking_constraints=True,
        constraint_adding_timeout=600000,
        solving_timeout=30000
):
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PRELIMINARIES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Start timer
    start_time = time.time()
    elapsed_time = -1

    result_dict = dict()

    # Extract useful info
    m = instance.n_couriers
    n = instance.n_items
    l = instance.max_loads
    s = instance.sizes
    d = instance.distances

    # Assertions defined in problem requirements
    assert n >= m, "The number of items should be greater or equal to the number of couriers!"
    assert sum(l) >= sum(s), "The total load exceeds the total capacity of couriers!"

    # Prepare ranges in format similar to minizinc
    ITEMS = range(n)
    COURIERS = range(m)
    LOCATIONS = range(n + 1)

    # Prepare solver
    solver_object = Solver()

    # Compute bits required to represent the integers in the problem
    # For the counted steps, the maximum number a courier will do is equal to the number of items
    steps_length = bit_requirement(n)

    # For the maximum distance, considering worst case scenario, when the maximum distance is made for each location
    worst_max_dist = 0
    for it in LOCATIONS:
        worst_max_dist += max([row[it] for row in d])
    max_distance_length = bit_requirement(worst_max_dist)

    # For the carried weight of courier, compute sum of all weights
    max_weight_length = bit_requirement(sum(s))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ VARIABLES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Item assignment to courier
    item_assignment = [[Bool(f"item_assignment_{i}_{j}") for i in ITEMS] for j in COURIERS]

    # Precedence table - mark with 1 if pre_table[i][j] = 1, 0 otherwise
    pre_table = [[Bool(f"pre_table_{i}_{j}") for i in ITEMS] for j in ITEMS]

    # Steps from origin - the number of STEPS (not dist) a courier made to deliver current item - for cycle breaking
    steps_from_origin = [[Bool(f"steps_from_origin_{i}_{j}") for j in range(steps_length)] for i in ITEMS]

    # Objective value
    max_dist = [Bool(f"max_dist_{i}") for i in range(max_distance_length)]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTRAINTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    distances_equal_to_max_dist = list()
    for courier in COURIERS:
        # Break max_load symmetry
        if not ignore_max_load_symmetry_breaking_constraints:
            for courier2 in range(courier + 1, m):
                if l[courier] == l[courier2]:
                    less_than(item_assignment[courier], item_assignment[courier2])

        # ENFORCE  COURIER  CAPACITY   &   COMPUTE  MAX  DIST
        # Variables for total carried weight and total distance of current courier
        carried_weight = [Bool(f'carried_weight_{courier}_{j}') for j in range(max_weight_length)]
        local_distance = [Bool(f'local_distance_{courier}_{j}') for j in range(max_distance_length)]

        # Lists of all the weights and distances
        # (the ones that are not of items carried by current courier marked with 0)
        carried_weights = list()
        all_distances = list()

        for item in ITEMS:
            if (time.time() - start_time) > (constraint_adding_timeout / 1000):
                result_dict["elapsed_time"] = ceil(elapsed_time)
                return result_dict, instance

            # Transform from integer to array of booleans (base 10 to base 2)
            local_weight = int_to_binary_arr(s[item], max_weight_length)

            # Add all the weights (enforce 0 for items not carried by current courier)
            carried_weights.append([And(item_assignment[courier][item], local_weight[i])
                                    for i in range(max_weight_length)])

            # Add all the distances
            # Add distance from origin if first item
            bin_dist = int_to_binary_arr(d[n][item], max_distance_length)
            all_distances.append([And(
                item_assignment[courier][item],
                exactly_zero(pre_table[item]),
                bin_dist[i]) for i in range(max_distance_length)])

            # Add distance from previous item
            for item2 in ITEMS:
                if item2 != item:
                    bin_dist = int_to_binary_arr(d[item2][item], max_distance_length)
                    all_distances.append([And(
                        item_assignment[courier][item],
                        pre_table[item][item2],
                        bin_dist[i]) for i in range(max_distance_length)])

            # Add distance to origin if last item
            bin_dist = int_to_binary_arr(d[item][n], max_distance_length)
            all_distances.append([And(
                item_assignment[courier][item],
                exactly_zero([row[item] for row in pre_table]),
                bin_dist[i]) for i in range(max_distance_length)])

        # Compute total carried weight
        solver_object.add(bin_arr_add(
            total=carried_weight,
            arr=carried_weights,
            length=max_weight_length,
            name=f"total_carried_weight_{courier}"
        ))

        # Make sure it's smaller than its capacity
        solver_object.add(less_or_eq(
            carried_weight,
            int_to_binary_arr(l[courier], max_weight_length)
        ))

        if (time.time() - start_time) > (constraint_adding_timeout / 1000):
            result_dict["elapsed_time"] = ceil(elapsed_time)
            return result_dict, instance

        # Compute total distance
        solver_object.add(bin_arr_add(
            total=local_distance,
            arr=all_distances,
            length=max_distance_length,
            name=f"local_distance_of_{courier}",
            timeout=constraint_adding_timeout,
            start_time=start_time
        ))

        if (time.time() - start_time) > (constraint_adding_timeout / 1000):
            result_dict["elapsed_time"] = ceil(elapsed_time)
            return result_dict, instance

        # Update max dist
        # Make sure all are smaller or equal
        solver_object.add(
            less_or_eq(local_distance, max_dist)
        )

        # Make sure at least one distance is equal to max dist
        distances_equal_to_max_dist.append(eq_to(local_distance, max_dist))
    solver_object.add(Or(distances_equal_to_max_dist))

    for it1 in ITEMS:
        if (time.time() - start_time) > (constraint_adding_timeout / 1000):
            result_dict["elapsed_time"] = ceil(elapsed_time)
            return result_dict, instance

        # [No improvement] Add upper domain boundary for steps_from_origin
        # solver_object.add(less_or_eq(steps_from_origin[it1], int_to_binary_arr(n, steps_length)))

        # Item cannot precede itself
        solver_object.add(Not(pre_table[it1][it1]))

        # Remove cycles - mark with 0 the number of steps done for first item
        solver_object.add(Implies(exactly_zero(pre_table[it1]), exactly_zero(steps_from_origin[it1])))

        # Each item assigned to a single courier
        solver_object.add(exactly_one([row[it1] for row in item_assignment], f"each_item_to_one_courier_{it1}"))

        for it2 in range(it1 + 1, n):
            # No 2 items with same precedent, unless coming from origin
            solver_object.add(Implies(
                Not(exactly_zero(pre_table[it1])),
                Not(eq_to(pre_table[it1], pre_table[it2]))
            ))

            solver_object.add(Implies(
                pre_table[it1][it2],
                And(
                    # Precedence only between items of the same courier - forward check
                    eq_to([row[it1] for row in item_assignment], [row[it2] for row in item_assignment]),

                    # Remove cycles - forward check
                    eq_to_plus_one(
                        steps_from_origin[it1],
                        steps_from_origin[it2],
                        length=steps_length,
                        name=f"forward_cycle_{it1}_{it2}"
                    )
                )
            ))

            # Each courier must have single item with origin as source
            solver_object.add(
                Implies(
                    eq_to([row[it1] for row in item_assignment], [row[it2] for row in item_assignment]),
                    And(
                        Implies(exactly_zero(pre_table[it1]), Or(pre_table[it2])),
                        Implies(exactly_zero(pre_table[it2]), Or(pre_table[it1])))
                )
            )

            solver_object.add(Implies(
                pre_table[it2][it1],
                And(
                    # Precedence only between items of the same courier - backward check
                    eq_to([row[it1] for row in item_assignment], [row[it2] for row in item_assignment]),

                    # Remove cycles - backward check
                    eq_to_plus_one(
                        steps_from_origin[it2],
                        steps_from_origin[it1],
                        length=steps_length,
                        name=f"backward_cycle_{it2}_{it1}")
                )
            ))

    # Break distances symmetry
    if not ignore_distance_symmetry_breaking_constraints:
        solver_object.add(less_or_eq(
            [pre_table[it1][it2] for it2 in ITEMS for it1 in ITEMS],
            [pre_table[it2][it1] for it2 in ITEMS for it1 in ITEMS]))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ SOLVING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print("Solving...")

    # Set left time
    initial_solving_timeout = solving_timeout
    start_time = time.time()

    while solving_timeout > 0:
        solver_object.set("timeout", int(max(solving_timeout, 0)))

        # Solve
        solver_status = solver_object.check()

        if solver_status == sat and solving_timeout >= 0:
            model = solver_object.model()

            # Extract data from model
            result_dict = {
                "item_assignment": list(),
                "pre_table": list(),
                "steps": list()
            }

            for row in item_assignment:
                result_dict["item_assignment"].append([model.evaluate(el) for el in row])

            for row in pre_table:
                result_dict["pre_table"].append([model.evaluate(el) for el in row])

            for row in steps_from_origin:
                result_dict["steps"].append([model.evaluate(el) for el in row])

            str_max_dist = ""
            actual_max_dist = [model.evaluate(max_dist[i]) for i in range(max_distance_length)]
            for el in actual_max_dist:
                str_max_dist += str(int(bool(el)))
            result_dict["max_dist"] = int(str_max_dist, 2)

            # Update greatest max dist found so far
            solver_object.add(less_than(max_dist, actual_max_dist))

            # Update time
            solving_timeout -= ((time.time() - start_time) * 1000)
            elapsed_time = initial_solving_timeout - solving_timeout
            start_time = time.time()
        elif solver_status == unsat:
            solving_timeout -= ((time.time() - start_time) * 1000)
            elapsed_time = initial_solving_timeout - solving_timeout
            break
        elif solver_status == unknown:
            elapsed_time = initial_solving_timeout
            break

    result_dict["elapsed_time"] = ceil(elapsed_time)
    return result_dict, instance
