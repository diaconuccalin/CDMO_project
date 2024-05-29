import time

from math import ceil, log2
from z3 import *


def int_to_binary_str(num, length=None):
    num_bin = bin(num).split("b")[-1]
    if length:
        return "0" * (length - len(num_bin)) + num_bin

    return num_bin


def str_to_binary_arr(bin_str):
    return [bool(int(bin_str[i])) for i in range(len(bin_str))]


def int_to_binary_arr(num, length=None):
    return str_to_binary_arr(int_to_binary_str(num, length))


def bit_requirement(x):
    return ceil(log2(x))


def less_than(a, b):
    eq_so_far = True
    already_less = False

    for i in range(len(a)):
        if i == len(a) - 1:
            return Or(
                And(eq_so_far, Not(a[i]), b[i]),
                already_less
            )
        else:
            already_less = Or(already_less, And(eq_so_far, Not(a[i]), b[i]))
            eq_so_far = And(eq_so_far, a[i] == b[i])


def eq_to(a, b):
    return And([a[i] == b[i] for i in range(len(a))])


def less_or_eq(a, b):
    return Or(less_than(a, b), eq_to(a, b))


def exactly_zero(x):
    return Not(Or(x))


def eq_to_plus_one(a, b, length, name):
    b_plus_one = [Bool(f'{name}_b_plus_one_{i}') for i in range(length)]

    return And(bin_add(b_plus_one, b, int_to_binary_arr(1, length), length, name), eq_to(a, b_plus_one))


def bin_add(d, a, b, length, name):
    c = [Bool(f'c_{name}_{i}') for i in range(length + 1)]

    fit_constraints = [Not(c[0]), Not(c[length])]

    c_constraints   = [
        c[i] == Or(
            And(a[i], b[i]),
            And(a[i], c[i + 1]),
            And(b[i], c[i + 1])
        ) for i in range(length)]

    d_constraints   = [
        d[i] == Or(
            And(a[i], b[i], c[i + 1]),
            And(a[i], Not(b[i]), Not(c[i + 1])),
            And(Not(a[i]), b[i], Not(c[i + 1])),
            And(Not(a[i]), Not(b[i]), c[i + 1])
        ) for i in range(length)]

    return And(fit_constraints + c_constraints + d_constraints)


def bin_arr_add(total, arr, length, name, timeout=None, start_time=None):
    constraints = list()

    prev_sum = None
    for idx, el in enumerate(arr):
        if (timeout is not None) and (time.time() - start_time) > (timeout / 1000):
            return And(constraints)
        local_sum = [Bool(f'local_sum_{name}_{idx}_{i}') for i in range(length)]

        if idx == 0:
            prev_sum = el
        elif idx == (len(arr) - 1):
            constraints.append(bin_add(
                total,
                prev_sum,
                el,
                length,
                f'{name}_{idx}'))
        else:
            constraints.append(bin_add(
                local_sum,
                prev_sum,
                el,
                length,
                f'{name}_{idx}'))
            prev_sum = local_sum

    return And(constraints)
