import argparse
import os
import torch
import sys
import torch.cuda as cuda
from colorama import Fore, Back, init
from methods import *
import multiprocessing as mp
init(True)

DEMO = True
VERSION_MSG = f"Effective Mark V2.0.0-alpha ({'demo' if DEMO else 'normal'})"

parser = argparse.ArgumentParser()
parser.add_argument('--test-type', dest='test_type', help='Select test type: STABILITY / BENCHMARK')
parser.add_argument('--target-device', dest='device', help='Select tested component: CPU / GPU / RAM')
parser.add_argument('--test-all', dest='runall', help='Run all test in order: CPU -> GPU -> RAM')
parser.add_argument('--report-results', dest='results', help='Enter filepath to save results')
args = parser.parse_args()

print(r"""----------------------------------------------------------------------------------+
                                                    *                                       |
      (     (                  )                  (  `                  )      )       )    |
 (    )\ )  )\ )    (       ( /( (    )      (    )\))(      )  (    ( /(   ( /(    ( /(    |
 )\  (()/( (()/(   ))\  (   )\()))\  /((    ))\  ((_)()\  ( /(  )(   )\())  )(_))   )\())   |
((_)  /(_)) /(_)) /((_) )\ (_))/((_)(_))\  /((_) (_()((_) )(_))(()\ ((_)\  ((_)    ((_)\    |
| __|(_) _|(_) _|(_))  ((_)| |_  (_)_)((_)(_))   |  \/  |((_)_  ((_)| |(_) |_  )   /  (_)   |
| _|  |  _| |  _|/ -_)/ _| |  _| | |\ V / / -_)  | |\/| |/ _` || '_|| / /   / /  _| () |    |
|___| |_|   |_|  \___|\__|  \__| |_| \_/  \___|  |_|  |_|\__,_||_|  |_\_\  /___|(_)\__/     |
--------------------------------------------------------------------------------------------+""")