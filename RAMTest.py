import random
import time

import psutil
import numpy as np
from colorama import Fore, init

init(True)
GOOD = Fore.GREEN
BAD = Fore.RED
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
chunk_num = round(RAM_FREE / chunk_size_b)

print("\nTest parameters:")
print(f"Chunk size:   {chunk_size_mb} MB")
print(f"Chunks used:  {chunk_num}")
print(f"Occupied RAM: {(chunk_num*chunk_size_b)/1024**3:.1f} GB")

done = False
passes = 0
errors = 0
while not done:
    try:
        pattern_raw = random.randint(0x01, 0xFF)
        pattern = np.full(chunk_size_b, pattern_raw, dtype=np.uint8)
        destination = np.empty_like(pattern)
        pattern.fill(pattern_raw)

        time.sleep(10)

        np.copyto(destination, pattern)

        if np.array_equal(pattern, destination):
            print(f"Test {passes + 1} ({str(pattern_raw).upper().replace('X', 'x')}): [{GOOD}PASSED{RESET}]")
        else:
            print(f"Test {passes + 1} ({str(pattern_raw).upper().replace('X', 'x')}): [{BAD}FAILED{RESET}]")


    except: pass