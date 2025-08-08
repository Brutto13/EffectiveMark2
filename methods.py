import time
import random
import os
import numpy as np
import torch
from math import sin, cos, tan, sqrt, log, pi
from statistics import mean


# Prepare CUDA drivers
# CUDA_PATH = r"P:\cuda-12.9"
# os.environ['NUMBAPRO_NVVM'] = os.path.join(CUDA_PATH, 'nvvm', 'bin', 'nvvm.dll')
# os.environ['NUMBAPRO_LIBDEVICE'] = os.path.join(CUDA_PATH, 'nvvm', 'libdevice', 'libdevice.10.bc')
# os.environ['PATH'] += os.pathsep + os.path.join(CUDA_PATH, 'bin')
# os.environ['PATH'] += os.pathsep + os.path.join(CUDA_PATH, 'lib', 'x64')


# from numba import cuda
# import arcade
# from pyglet.event import EVENT_HANDLE_STATE
# from OpenGL.GL import glGetString, GL_RENDERER

# print(cuda.detect())

def get_time(*, precision: int = 1):
    """
    Simple decorator measuring execution time
    """
    def _outer(func):
        def _inner(*args, **kwargs):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            elapsed = round(end - start, precision)
            return elapsed
        return _inner
    return _outer


def get_avg(func):
    """Decorator that returns mean of received list"""
    def _inner(*args, **kwargs):
        result = func(*args, **kwargs)
        return mean(result)
    return _inner


@get_time(precision=3)
def cpu_test(iterations: int = int(1e9)):
    results = []
    for i in range(iterations):
        x = log(abs(sin(sqrt(i)-cos(i+1))-tan(i % 90)**log(i+1, 3))+1, pi)
        results.append(x)
    n = sum(results)
    return n


def cpu_multithreaded(values, iterations: int = int(1e9)):
    results = []
    start = time.perf_counter()
    for i in range(iterations):
        x = log(abs(sin(sqrt(i)-cos(i+1))-tan(i % 90)**log(i+1, 3))+1, pi)
        results.append(x)
    n = sum(results)
    values.append(time.perf_counter() - start)


@get_time(precision=3)
def test_gpu(device: str, n: int = int(1e4), i: int = 10000):
    device = torch.device(device)
    print(f'Using device: {device}')
    for x in range(i):
        # Create tensors on GPU
        a = torch.randn(n, n, device=device)
        b = torch.randn(n, n, device=device)

        # Arithmetic on GPU
        c = a + b

