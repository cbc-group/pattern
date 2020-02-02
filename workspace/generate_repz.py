import logging
import os

import coloredlogs

from pattern.slm.fourthdd import ActivationMethod, FrameGroup, Repertoire, RunningOrder

logger = logging.getLogger(__name__)

coloredlogs.install(
    level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
)

sequence_lib = "test_repz_src/sequences"
image_lib = "test_repz_src/images"

sequence = "48071 HHMI 50ms"
images = [os.path.splitext(p)[0] for p in os.listdir(image_lib)]

start_fg = FrameGroup(loop=False)
for i, image in enumerate(images):
    start_fg.add_frame(sequence, image, wait_trigger=(i == 0))

loop_fg = FrameGroup(loop=True)
for image in images:
    loop_fg.add_frame(sequence, image)

ro = RunningOrder(ActivationMethod.Hardware)
ro.add_frame_group(start_fg)
ro.add_frame_group(loop_fg)

rep = Repertoire(sequence_lib, image_lib)
rep["sequential tiles"] = ro

print(rep.compile())
