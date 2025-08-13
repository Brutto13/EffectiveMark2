# EffectiveMark2 toolkit
This software is a toolkit designed especially for checking stability of overclocked components.
This includes CPU, RAM, GPU and VRAM tests. All have built-in error detection.

## CPU Test (CPUTest.py)
This test takes no command-line arguments. Classic CPU test launches as many processes
as CPU cores are detected. It uses CPU to calculate arithmetic operations on number and compares
it with precalculated results.

## RAM Test (RAMTst.py)
**WARNING: This test is NOT as accurate as Memtest86, **but it's good enough to test
R/W operations on system**

## GPU Test (GPUTest.py)
Test written in OpenCL, so it **should** work on both AMD and NVIDIA cards.
Loads GPU with arithmetic operations which uses low amounts of VRAM which is useful when debugging
overclocking problems. This test accepts following arguments from command line:
- `--target-device`, `-td`: For multi-gpu setup ONLY. Select which card should be tested.
**This argument doesn't accept names like "NVIDIA GTX 1080 Ti** It accepts IDs like "0" (means GPU-0)

## VRAM test (VRAMTest.py)
This test works similar to RAM test. Writes known pattern. then loads GPU with calculations that
do not use VRAM. After computations are complete it reads VRAM pattern and check if it's still the same.
Following arguments are accepted:
- `--target-device`, `-td`: Tested device's ID (multi-gpu setup ONLY)
- `--chunk-size`, `-cs`: Test uses "chunks" to control and fill VRAM. Smaller number will take more time to fill
but can be more precise while calculating number of chunks. E.g. Assuming 6GB VRAM and chunk size is set to 512.
Quick calculations shows, that using 10 chunks will fill 5120MB VRAM. Setting this to 256 or 128
will use more chunks but can use more VRAM
- `--load-loops`, `-ll`: This parameter defines how many times GPU will be "asked" to calculate some data. If test freezes 
or takes too long reducing this value can help
- `--free-space`, `-fs`: How much memory should be unallocated. If you are hitting `OOMError` raising this
value can help.
- `--warmup-temp`, `-wt`: Temperature that must be reached by GPU before continuing, allows simulation of
thermal edge- and worst-case scenarios.

## Render Test (torus_test.py)
Uses GPU to render rotating torus with moving light which uses
a lot of calculations. this is very aggressive GPU test which allows to see
rendering artifacts.

## Thermal Test (GPUTempTest.py)
This test measures how fast the GPU heats up. It will stop on 85*C or other temperature is specified
in args

## Summary
These test should be enough if you want to quickly check for most common
errors caused by overclocking or degradation of components. It's definitely
**NOT** enough to have 100% confidence of stable system (yet).
This test does **NOT** provide GPU temperature / power consumption
monitoring. This monitoring is written in "SysView" project.
Practical information: ANY failed test means system instability even occasional
ones. One test is **NOT** enough to judge system stability, but if GPU passes around 200-300
test loops without any errors it's strong sign that everything is OK.