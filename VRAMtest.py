import random
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

parser = argparse.ArgumentParser()
parser.add_argument('--target-device', '-d', dest='target', required=False, default=0, help='For multi-GPU setup. Select device ID')
parser.add_argument('--chunk-size', dest='_chunk_size', required=False, default=512, help='Change chunk size used to fill memory')
args = parser.parse_args()

try: device_id = int(args.target)
except ValueError:
    print(BAD + "Incorrect argument passed! Assuming default ID: 0")
    device_id = 0

target_vram = round(GPUtil.getGPUs()[device_id].memoryTotal, -3)
platform = cl.get_platforms()[0]
device = platform.get_devices()[device_id]
ctx = cl.Context([device])
queue = cl.CommandQueue(ctx)


# Buffer size
chunk_size = 512  # [MB]
chunk_size_bytes = 512*(1024**2)  # [B]
num_chunks = int(target_vram/chunk_size)-1
print(f"Chunks: {num_chunks}")
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
    raw_bytes = random.randint(0x01, 0xFF)
    pattern.fill(raw_bytes)

    try:
        # Allocate VRAM
        for i in range(num_chunks):
            buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=chunk_size_bytes)
            assert pattern.nbytes == chunk_size_bytes  # TODO: Check it as condition and mark test as FAILED on mismatch
            cl.enqueue_copy(queue, buf, pattern[:], is_blocking=True)
            buffers.append(buf)
            print(f"Status: Chunk {i+1} / {num_chunks} allocated", end='\r')
        # print(f"Chunk {num_chunks} / {num_chunks} allocated!")

        print("Sleeping 15s...                     ", end='\r')
        time.sleep(15)
        print("Reading from VRAM...", end='\r')
        for i, buf in enumerate(buffers):
            readback = np.empty_like(pattern)

            # Copy data to RAM
            cl.enqueue_copy(queue, readback, buf, is_blocking=True)

            # Check integrity
            if not numpy.all(readback == raw_bytes):
                error = True
        loop += 1

    except cl.MemoryError:
        print("OOMError: Out of memory!")
        done = True

    except KeyboardInterrupt:
        print("Test stopped by user request (CTRL+C)")
        print(f"Test passes: {loop}")
        input("PRESS ENTER TO CLOSE")
        done = True

    finally:
        # Cleanup VRAM for next test
        print("Clearing VRAM", end='\r')
        buffers.clear()
        gc.collect()
        print("VRAM Clear!   ", end='\r')
        # time.sleep(2)
        if not error: print(f"Test {loop} ({ADDR}{hex(raw_bytes).upper().replace('X', 'x')}{RESET}): [{GOOD}PASSED{RESET}]\t\t")
        else: print(f"Test {loop} ({ADDR}{hex(raw_bytes).upper().replace('X', 'x')}{RESET}) [{BAD}FAILED{RESET}]\t\t")
