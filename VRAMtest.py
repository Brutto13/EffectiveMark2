import random
import sys
import time
import GPUtil
import argparse
import gc
import numpy
import numpy as np
import pyopencl as cl
from colorama import Fore, init

init(True)

GOOD = Fore.GREEN
BAD = Fore.RED
ADDR = Fore.YELLOW
RESET = Fore.RESET

parser = argparse.ArgumentParser(
    prog="EffectiveMark2 - Stability testing toolkit",
    description="VRAM testing application",
    allow_abbrev=False,

)
parser.add_argument('--target-device', '-td', dest='target', required=False, default=0, help='For multi-GPU setup. Select device ID')
parser.add_argument('--chunk-size', '-cs', dest='chunk_size', required=False, default=512, help='Change chunk size used to fill memory')
parser.add_argument('--load-loops', '-ll', dest='loops', required=False, default=2000, help='Number of load loops')
parser.add_argument('--free-space', '-fs', dest='free', required=False, default=1000, help='Unallocated VRAM memory')
parser.add_argument('--warmup-temp', '-wt', dest='t_temp', required=False, default=50, help='NVIDA only: Warm GPU to this temperature before entering temperatures')
parser.add_argument('--aggressive-timing', '-at', dest='no_timeout', required=False, default=False, action='store_true', help='Disable timeout between tests')
args = parser.parse_args()

try: device_id = int(args.target)
except ValueError:
    print(BAD + "Incorrect argument passed! Assuming default ID: 0")
    device_id = 0

# OpenCL context
target_vram = round(GPUtil.getGPUs()[device_id].memoryTotal, 1)-1000
platform = cl.get_platforms()[0]
device = platform.get_devices()[device_id]
ctx = cl.Context([device])
queue = cl.CommandQueue(ctx)

# Setup args
try: loads = int(args.loops)
except ValueError:
    print(F"{BAD}ValueError{RESET}: {ADDR}Invalid --load-loops argument. Assuming default value!")
    loads = int(1e4)

# Buffer size
try: chunk_size = int(args.chunk_size)  # [MB]
except ValueError:
    print(F"{BAD}ValueError{RESET}: {ADDR}Invalid --chunk-size argument. Assuming default value!")
    chunk_size = 512

try: target_temp = float(args.t_temp)
except ValueError:
    print(F"{BAD}ValueError{RESET}: {ADDR}Invalid --warmup-temp argument. Assuming default value!")
    target_temp = 50

chunk_size_bytes = chunk_size*(1024**2)  # [B]
num_chunks = int(target_vram/chunk_size)

# num_chunks = 10

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
print(f"Target VRAM: {target_vram}")
print(f"Chunks:      {num_chunks}")
print(f"Chunk size:  {chunk_size}MB")

# Prepare kernel
KERNEL = """
__kernel void compute(__global float* data) {
    int i = get_global_id(0);
    float x = data[i];

    for (int j = 0; j < 1000; ++j) {
        float safe = fmax(x + 1.0f, 1e-6f);
        x = sin(cos(x)) * cos(sin(x)) + sqrt(fabs(x)) + log(safe);

        if (isnan(x) || isinf(x)) {
            x = 0.0f;
            break;
        }
    }

    data[i] = x;
}

__kernel void warmup(__global float* data) {
    int i = get_global_id(0);
    float x = data[i];

    // Simulate heavy math
    for (int j = 0; j < 1000; ++j) {
        x = sin(cos(x)) * cos(sin(x)) + sqrt(fabs(x)) + log(x + 1.0f);
    }

    data[i] = x;
}

"""

N = 1024 * 1024 * 32
global_size = (N,)
local_size = None
gpu_number = np.ones(98360, dtype=np.float16)
gpu_num_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=gpu_number)

program = cl.Program(ctx, KERNEL).build()
process = cl.Kernel(program, 'compute')
warmup  = cl.Kernel(program, 'warmup')

data_np = np.random.rand(N)

print("Launching VRAM test")
print(f"Tested device: {device.name}")
print(f"Tested VRAM:   {num_chunks*chunk_size} MB")

buffers = []
done = False
loop = 0

# Load data
try:
    data_np = np.load("bin/input.npy")
except:
    data_np = np.load(f"{sys._MEIPASS}\\bin\\input.npy")


# Warmup
warmed = False
mf = cl.mem_flags
data = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=data_np)
while not warmed:
    current_temp = GPUtil.getGPUs()[device_id].temperature
    warmup(queue, (1024 * 1024 * 256,), None, data)
    print(f"Warming up GPU: {current_temp} *C / {target_temp} *C", end='\r')
    queue.finish()

    if current_temp >= target_temp:
        warmed = True
        # Clear previous labels
        print("                                   ", end='\r')

# VRAM test
while not done:
    error = False

    # Change pattern each time
    pattern = np.empty(chunk_size_bytes, dtype=np.uint8)
    raw_bytes = random.randint(0x00, 0xFF)
    pattern.fill(raw_bytes)

    try:
        # Allocate VRAM
        for i in range(num_chunks):
            buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=chunk_size_bytes)
            cl.enqueue_copy(queue, buf, pattern[:], is_blocking=True)
            buffers.append(buf)
            print(f"Status: Chunk {i+1} / {num_chunks} allocated", end='\r')

        for n in range(loads):
            process(queue, (98360,), None, gpu_num_buf)
            print(f"Generating GPU Load ({n+1} / {loads})", end='\r')
            queue.finish()

        print("Reading from VRAM...           ", end='\r')
        for i, buf in enumerate(buffers):
            readback = np.empty_like(pattern)

            # Copy data to RAM
            cl.enqueue_copy(queue, readback, buf, is_blocking=True)
            queue.finish()

            # Check integrity
            if not numpy.all(readback == raw_bytes):
                error = True

            # Cleanup VRAM for next test
            print("Clearing VRAM", end='\r')
            buffers.clear()
            gc.collect()
            print("VRAM Clear!   ", end='\r')

            # Logging
            addr_str = hex(raw_bytes).upper().replace('X', 'x')
            if len(addr_str) == 3:
                addr_str = addr_str.replace('x', 'x0')

            if not error: print(f"Test {loop+1} ({ADDR}{addr_str}{RESET}): [{GOOD}PASSED{RESET}]             ")
            else: print(f"Test {loop+1} ({ADDR}{addr_str}{RESET}) [{BAD}FAILED{RESET}]                ")
            if not args.no_timeout: time.sleep(5)

        loop += 1

    except cl.MemoryError:
        print(f"{BAD}OOMError{RESET}: {ADDR}Out of memory!{RESET}")
        input("PRESS ENTER TO CLOSE!")
        done = True

    except KeyboardInterrupt:
        print("Test stopped by user request (CTRL+C)")
        print(f"Test passes: {loop+1}")
        input("PRESS ENTER TO CLOSE")
        done = True
