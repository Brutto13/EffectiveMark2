import os
import sys
import multiprocessing as mp
import random

from colorama import Fore, init

init(True)
GOOD = Fore.GREEN
BAD = Fore.RED
RESET = Fore.RESET

from methods import *

# Multiprocessing needs this condition
if __name__ == '__main__':
    mp.freeze_support()
    print(r"""
    +---------------------------------------------------------------------------------------------+
    |                                                     *                                       |
    |       (     (                  )                  (  `                  )      )       )    |
    |   (    )\ )  )\ )    (       ( /( (    )      (    )\))(      )  (    ( /(   ( /(    ( /(   |
    |  )\  (()/( (()/(   ))\  (   )\()))\  /((    ))\  ((_)()\  ( /(  )(   )\())  )(_))   )\())   |
    | ((_)  /(_)) /(_)) /((_) )\ (_))/((_)(_))\  /((_) (_()((_) )(_))(()\ ((_)\  ((_)    ((_)\    |
    | | __|(_) _|(_) _|(_))  ((_)| |_  (_)_)((_)(_))   |  \/  |((_)_  ((_)| |(_) |_  )   /  (_)   |
    | | _|  |  _| |  _|/ -_)/ _| |  _| | |\ V / / -_)  | |\/| |/ _` || '_|| / /   / /  _| () |    |
    | |___| |_|   |_|  \___|\__|  \__| |_| \_/  \___|  |_|  |_|\__,_||_|  |_\_\  /___|(_)\__/     |
    +---------------------------------------------------------------------------------------------+""")
    cores_num = os.cpu_count()
    print(f"CPU Cores: {cores_num}")

    try:
        with open(R"bin\cpu_results.bin", "r") as file:
            responses = file.read().split(';')
    except FileNotFoundError:
        with open(f"{sys._MEIPASS}\\bin\\cpu_results.bin", "r") as file:
            responses = file.read().split(';')

    done = False
    loop = 1
    while not done:
        try:
            x_value = random.randint(0, 36474)
            manager = mp.Manager()
            values = manager.list()
            processes = []
            for p in range(cores_num):
                proc = mp.Process(target=cpu_multithreaded, args=(x_value, values))
                processes.append(proc)
                proc.start()

            # Wait until process terminates
            for proc in processes:
                proc.join()

            expected = responses[x_value]

            failed_cores = []
            for core in range(cores_num):
                if values[core] != float(expected):
                    failed_cores.append(core)

            if len(failed_cores) == 0:
                print(f"Test {loop}: [{GOOD}PASSED{RESET}]")
            else:
                print(f"Test {loop}: [{BAD}FAILED{RESET}] (Cores: {str(failed_cores)[1:-1].replace(', ', ' ')})")

            loop += 1

        except KeyboardInterrupt:
            print("Stopped by user request!")
            input("PRESS ENTER TO CLOSE")
            done = True

