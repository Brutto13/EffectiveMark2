import time
import GPUtil
import argparse
import gc
import numpy as np
import pyopencl as cl
from colorama import Fore, init

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument('--target-device', '-td', dest='target', required=False, default=0, help='Target device\'s ID')
parser.add_argument('--target-temp', '-tt', dest='target_temp', required=False, default=85, help='Temperature, that means test completion')
parser.add_argument('--logging-delta', '-ld', dest='log_delta', required=False, default=5, help='Logging frequency')
args = parser.parse_args()

# Setup colors
init(True)
GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
RED = Fore.RED
CYAN = Fore.CYAN
LCYAN = Fore.LIGHTCYAN_EX
DIMMED = Fore.LIGHTBLACK_EX
RESET = Fore.RESET

# arguments post-processing
try: device_id = int(args.target)
except ValueError:
    print(f"{RED}ValueError{RESET}:{YELLOW}Expected valid device ID, Assuming default value!{RESET}")
    device_id = 0

try: target_temp = int(args.target_temp)
except ValueError:
    print(f"{RED}ValueError{RESET}:{YELLOW}Expected valid temperature [*C], Assuming default value!{RESET}")
    target_temp = 85

try: log_delta = int(args.log_delta)
except ValueError:
    print(f"{RED}ValueError{RESET}:{YELLOW}Expected valid number , Assuming default value!{RESET}")
    log_delta = 5

# Setup OpenCL
platform = cl.get_platforms()[0]
device = platform.get_devices()[device_id]
ctx = cl.Context([device])
queue = cl.CommandQueue(ctx)

KERNEL = """
__kernel void warmup(__global float* data) {
    int i = get_global_id(0);
    float x = data[i];

    // Simulate heavy math
    for (int j = 0; j < 100; ++j) {
        x = sin(cos(x)) * cos(sin(x)) + sqrt(fabs(x)) + log(x + 1.0f);
    }

    data[i] = x;
}
"""

program = cl.Program(ctx, KERNEL).build()
process = cl.Kernel(program, 'warmup')

# Generate data
mf = cl.mem_flags
N = 1024 * 1024 * 1024
global_size = (N,)
local_size = None
# gpu_number = np.ones(98360, dtype=np.float16)
data_np = np.random.rand(N)
data = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=data_np)


# Setup GPUtil


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

# Main test loop
start = time.perf_counter()
printed_temps = []
processing = True
while processing:
    try:
        # Processing on GPU
        process(queue, (N,), None, data)
        queue.finish()

        # Check temperature
        gpu = GPUtil.getGPUs()[device_id]
        current_temp = gpu.temperature
        if current_temp >= target_temp: processing = False
        if current_temp % log_delta == 0 and current_temp not in printed_temps:
            # Logging every 5*C delta
            elapsed = time.perf_counter()-start
            SECONDS = elapsed % 60
            MINUTES = elapsed / 60
            HOURS   = MINUTES / 60
            if MINUTES <= 1: time_str = f"{SECONDS:.1f}s"
            elif 1 <= MINUTES < 60: time_str = f"{MINUTES:.1f}m"
            elif MINUTES >= 60: time_str = f"{HOURS:.1f}h"
            # else: time_str = "N/A"

            print(F"Temperature: {YELLOW}{current_temp}{RESET} *C reached in {CYAN}{time_str}{RESET}")
            printed_temps.append(current_temp)
        else:
            print(F"Temperature: {YELLOW}{current_temp}{RESET} *C", end='\r')

    except cl.MemoryError:
        print(F"{RED}OOMError{RESET}: {YELLOW}Out of memory!{RESET}")
        input()
        processing = False

    except KeyboardInterrupt:
        print("Cooling down...      ")
        processing = False

cooling = True
printed_temps = []
start = time.perf_counter()
while cooling:
    gpu = GPUtil.getGPUs()[device_id]
    current_temp = gpu.temperature

    if current_temp % log_delta == 0 and current_temp not in printed_temps:
        elapsed = time.perf_counter() - start
        SECONDS = elapsed % 60
        MINUTES = elapsed / 60
        HOURS = MINUTES / 60
        if MINUTES <= 1:
            time_str = f"{SECONDS:.1f}s"
        elif 1 <= MINUTES < 60:
            time_str = f"{MINUTES:.1f}m"
        elif MINUTES >= 60:
            time_str = f"{HOURS:.1f}h"
        print(F"Temperature: {LCYAN}{current_temp}{RESET} *C reached in {CYAN}{time_str}{RESET}")
        printed_temps.append(current_temp)
    else:
        print(f"Temperature: {LCYAN}{current_temp}{RESET} *C", end='\r')




