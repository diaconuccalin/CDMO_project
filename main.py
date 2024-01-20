import os
import subprocess
import time

from src.io_stream import write_to_json


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

    with open("reports/report" + str(max_report + 1), "w") as fout:
        for el in os.listdir(the_dir):
            print(el)
            data_path = os.path.join(the_dir, el)

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

            inst_n = el[-6:-3]
            if "UNKNOWN" in output:
                fout.write(inst_n + " - R: UNK - T: " + str(time_delta) + "\n")
            else:
                fout.write(inst_n + " - R: " + output[output.rfind("dist = ") + len("dist = "):output.rfind(";")] + " - T: " + str(time_delta) + "\n")

            write_to_json(output, inst_n, str(max_report + 1), time_delta)

    return None


if __name__ == "__main__":
    main()
