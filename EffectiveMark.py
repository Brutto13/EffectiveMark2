import argparse
from colorama import Fore, Back, init
init(True)

VERSION_MSG = "Effective Mark V2.0.0-alpha (demo)"

parser = argparse.ArgumentParser()
parser.add_argument("--disable-cpu", dest='nocpu', required=False, default=False, action='store_true', help="Skip CPU test")
parser.add_argument("--disable-gpu", dest='nogpu', required=False, default=False, action='store_true', help="Skip GPU test")
parser.add_argument("--disable-ram", dest='noram', required=False, default=False, action='store_true', help="Skip RAM test")
parser.add_argument("--suppress-color", dest='nocolor', required=False, default=False, action='store_true', help="Disable color output")
parser.add_argument("--manual-config", dest='maual', required=False, default=False, action='store_true', help="Launch settings")
parser.add_argument("--no-confirm", dest='noconfirm', required=False, default=False, action='store_true', help="Skips EVERY confirmation dialog")
parser.add_argument("--version", dest='verexit', required=False, default=False, action='store_true', help="Print Version and exit")
args = parser.parse_args()

config = {
    'skip': {
        'cpu': args.nocpu,
        'gpu': args.nogpu,
        'ram': args.noram
    },

    'exit': {
        'version': args.verexit
    },

    'confirm': not args.noconfirm,
    'color': not args.nocolor,
}

INFO = Fore.CYAN
WARN = Fore.YELLOW
ERROR = Fore.RED
FATAL = Back.RED + Fore.WHITE
DEBUG = Fore.GREEN

print(r"""
                                                    *                                     
      (     (                  )                  (  `                  )      )       )  
 (    )\ )  )\ )    (       ( /( (    )      (    )\))(      )  (    ( /(   ( /(    ( /(  
 )\  (()/( (()/(   ))\  (   )\()))\  /((    ))\  ((_)()\  ( /(  )(   )\())  )(_))   )\()) 
((_)  /(_)) /(_)) /((_) )\ (_))/((_)(_))\  /((_) (_()((_) )(_))(()\ ((_)\  ((_)    ((_)\  
| __|(_) _|(_) _|(_))  ((_)| |_  (_)_)((_)(_))   |  \/  |((_)_  ((_)| |(_) |_  )   /  (_) 
| _|  |  _| |  _|/ -_)/ _| |  _| | |\ V / / -_)  | |\/| |/ _` || '_|| / /   / /  _| () |  
|___| |_|   |_|  \___|\__|  \__| |_| \_/  \___|  |_|  |_|\__,_||_|  |_\_\  /___|(_)\__/  
""")

# TODO: CPU Benchmark
if config["confirm"]:
    _confirm = input("Launch CPU Benchmark [Y\\n]: ")
    if _confirm != "Y":
        print()

# TODO: GPU Benchmark
# TODO: RAM Benchmark
# TODO: Manual configuration
