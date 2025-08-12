import random
import time
import GPUtil
import sys
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

parser = argparse.ArgumentParser()
parser.add_argument('--target-device', '-td', dest='target', required=False, default=0, help='For multi-GPU setup. Select device ID')
parser.add_argument('--chunk-size', '-cs', dest='chunk_size', required=False, default=512, help='Change chunk size used to fill memory')
parser.add_argument('--load-loops', '-ll', dest='loops', required=False, default=10000, help='Number of load loops')
parser.add_argument('--free-space', '-fs', dest='free', required=False, default=1000, help='Unallocated VRAM memory')
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
}"""

N = 1024 * 1024 * 32
global_size = (N,)
local_size = None
gpu_number = np.ones(98360, dtype=np.float16)
gpu_num_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=gpu_number)

program = cl.Program(ctx, KERNEL).build()
process = cl.Kernel(program, 'compute')

data_np = np.random.rand(N)

print("Launching VRAM test")
print(f"Tested device: {device.name}")
print(f"Tested VRAM:   {num_chunks*chunk_size} MB")

buffers = []
done = False
loop = 0
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
        # print(f"Chunk {num_chunks} / {num_chunks} allocated!")

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
            time.sleep(5)

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
