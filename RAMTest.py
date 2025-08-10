import random
import time

import psutil
import numpy as np
from colorama import Fore, init

init(True)
GOOD  = Fore.GREEN
BAD   = Fore.RED
ADDR  = Fore.YELLOW
RESET = Fore.RESET

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

RAM_FREE = psutil.virtual_memory().free

print("Launching RAM Test")
print(f"Detected {RAM_FREE/(1024**3):.1f} GB free RAM memory")

# 512MB chunk size
chunk_size_mb = 512  # [MB]
chunk_size_b = 1024 * 1024 * chunk_size_mb  # [B]

# Calculate chunks needed to fill memory
chunk_num = round(RAM_FREE / chunk_size_b)//2
# chunk_num = 10
print("\nTest parameters:")
print(f"Chunk size:   {chunk_size_mb} MB")
print(f"Chunks used:  {chunk_num}")
print(f"Occupied RAM: {(chunk_num*chunk_size_b)/1024**3:.1f} GB")

done = False
passes = 0
errors = 0
while not done:
    try:
        from_buffers = []
        destination_buffers = []
        pattern_raw = random.randint(0x01, 0xFF)

        for i in range(chunk_num):
            pattern = np.full(chunk_size_b, pattern_raw, dtype=np.uint8)
            pattern.fill(pattern_raw)
            from_buffers.append(pattern)
            print(f"Filling RAM ({i+1} / {chunk_num})", end='\r')

        print("Sleeping 10s               ", end='\r')
        time.sleep(10)

        for buff_idx, buff in enumerate(from_buffers):
            destination = np.empty_like(buff)
            np.copyto(destination, buff)
            destination_buffers.append(destination)
            print(f"Copying data ({buff_idx+1} / {len(from_buffers)})", end='\r')

        print("Sleeping 10s                ", end='\r')
        time.sleep(10)

        for src_idx, dest in enumerate(destination_buffers):
            print(f"Verifying data ({src_idx+1} / {len(destination_buffers)})", end='\r')
            if not np.array_equal(dest, from_buffers[src_idx]): errors += 1

        if errors != 0:
            print(f"Test {passes + 1} ({ADDR}{hex(pattern_raw).upper().replace('X', 'x')}{RESET}): [{BAD}FAILED{RESET}]    ")
        else:
            print(f"Test {passes + 1} ({ADDR}{hex(pattern_raw).upper().replace('X', 'x')}{RESET}): [{GOOD}PASSED{RESET}]    ")

        time.sleep(3)
        passes += 1

    except KeyboardInterrupt:
        input("PRESS ENTER TO CLOSE")
        done = True

    except Exception as e:
        print(f"ERROR: {e}")
        input()
