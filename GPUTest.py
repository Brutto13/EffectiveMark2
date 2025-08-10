import argparse
import sys
import pyopencl as cl
import numpy as np
from colorama import Fore, init

init(True)
GOOD = Fore.GREEN
BAD = Fore.RED
RESET = Fore.RESET

parser = argparse.ArgumentParser()
parser.add_argument('--target-device', '-td', dest='target', required=False, default=0, type=int, help='Select target device ID')
args = parser.parse_args()

device_id = args.target

# Setup OpenCL
platform = cl.get_platforms()[0]
device = platform.get_devices()[device_id]
ctx = cl.Context([device])
queue = cl.CommandQueue(ctx)

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

print(f"Tested GPU: {device.name}")

KERNEL = """
__kernel void compute(__global float* data) {
    int i = get_global_id(0);
    float x = data[i];
    
    // Simulate heavy math
    for (int j = 0; j < 1000; ++j) {
        x = sin(cos(x)) * cos(sin(x)) + sqrt(fabs(x)) + log(x + 1.0f);
    }

    data[i] = x;
}"""

# Calculate data

program = cl.Program(ctx, KERNEL).build()
process = cl.Kernel(program, 'compute')

done = False
passes = 1
errors = 0

N = 1024 * 1024 * 256
global_size = (N,)
local_size = None

print("Loading data...")
try:
    data_np = np.load("bin/input.npy")
    expect_np = np.load("bin/output.npy")
except:
    data_np = np.load(f"{sys._MEIPASS}\\bin\\input.npy")
    expect_np = np.load(f"{sys._MEIPASS}\\bin\\output.npy")

print("starting test...")
while not done:
    try:
        # Allocate memory
        mf = cl.mem_flags
        data = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=data_np)
        # c = cl.Buffer(ctx, mf.WRITE_ONLY, size=result_np.nbytes)
        print("Calculating...", end='\r')
        process(queue, (N,), None, data)
        queue.finish()

        print("Downloading results...", end='\r')
        result_np = np.empty_like(data_np)
        cl.enqueue_copy(queue, result_np, data)
        queue.finish()

        print("Verifying results...", end='\r')
        if not np.array_equal(result_np, expect_np): print(f"Test {passes}: [{BAD}FAILED{RESET}]           "); errors += 1
        else: print(f"Test {passes}: [{GOOD}PASSED{RESET}]           ")
        passes += 1

    except KeyboardInterrupt:
        print("Stopped by user request!")
        print("-------+ Statistics +-------")
        print(f"Passes: {passes}")
        print(f"Errors: {errors} ({round((errors/passes)*100, 1)}%)")
        input("--+ Press enter to close +--")
        done = True
