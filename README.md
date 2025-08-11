# EffectiveMark2 toolkit
This software is a toolkit designed especially for checking stability of overclocked components.
This includes CPU, RAM, GPU and VRAM tests. All have built-in error detection.

## CPU Test
This test takes no command-line arguments. Classic CPU test launches as many processes
as CPU cores are detected. It uses CPU to calculate arithmetic operations on number and compares
it with precalculated results.

## RAM Test
**WARNING: This test is NOT as accurate as Memtest86** but it's good enough to test
R/W operations on system

## GPU Test
Test written in OpenCL, so it **should** work on both AMD and NVIDIA cards.
Loads GPU with arithmetic operations which uses low amounts of VRAM which is useful when debugging
overclocking problems. This test accepts following arguments from command line:
- `--target-device`, `-td`: For multi-gpu setup ONLY. Select which card should be tested.
**This argument doesn't accept names like "NVIDIA GTX 1080 Ti** It accepts IDs like "0" (means GPU-0)

## VRAM test
This test works similar to RAM test. Writes known pattern. then loads GPU with calculations that
do not use VRAM. After computations are complete it reads VRAM pattern and check if it's still the same.
Following arguments are accepted:
- `--target-device`: Tested device's ID (multi-gpu setup ONLY)
- `--chunk-size`: Test uses "chunks" to control and fill VRAM. Smaller number will take more time to fill
but can be more precise while calculating number of chunks. E.g. Assuming 6GB VRAM and chunk size is set to 512.
Quick calculations shows, that using 10 chunks will fill 5120MB VRAM. Setting this to 256 or 128
will use more chunks but can use more VRAM
- `--load-loops`: This parameter defines how many times GPU will be "asked" to calculate some data. If test freezes 
or takes too long reducing this value can help
- `--free-space`: How much memory should be unallocated. If you are hitting `OOMError` raising this
value can help.