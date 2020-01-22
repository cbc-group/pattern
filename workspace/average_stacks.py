import glob
import os

import imageio
import numpy as np

src_dir = "S:/Andy/tiling_pattern_trials/NA0.2294_na0.1613_45b_s3p0254_t0"

file_list = glob.glob(os.path.join(src_dir, "*CamB*.tif"))
file_list.sort()

file_list = file_list[:8]
stack_average = None
for file_path in file_list:
    stack = imageio.volread(file_path)
    try:
        stack_average += stack
        stack_average /= 2
    except Exception:
        stack_average = stack.astype(np.float32)

imageio.volwrite("averaged.tif", stack_average)
