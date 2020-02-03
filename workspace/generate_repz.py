from datetime import datetime
import logging
import os

import coloredlogs

from pattern.slm.fourthdd import (
    ActivationMethod,
    FrameGroup,
    Repertoire,
    RepertoireArchive,
    RunningOrder,
)

logger = logging.getLogger(__name__)

coloredlogs.install(
    level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
)

## library
sequence_lib = "test_repz_src/sequences"
image_lib = "test_repz_src/images"

## data source
sequence = "48071 HHMI 50ms"
images = [os.path.splitext(p)[0] for p in os.listdir(image_lib)]
images.sort()
logger.info(f"{len(images)} image(s) in the library")

## template
rep = Repertoire(sequence_lib, image_lib)

## build ro1
start_fg = FrameGroup(loop=False)
for i, image in enumerate(images):
    start_fg.add_frame(sequence, image, wait_trigger=(i == 0))

loop_fg = FrameGroup(loop=True)
for image in images:
    loop_fg.add_frame(sequence, image)

ro = RunningOrder(ActivationMethod.Hardware)
ro.add_frame_group(start_fg)
ro.add_frame_group(loop_fg)

rep["sequential tiles"] = ro

## build ro2
fg = FrameGroup(loop=True)
fg.add_frame(sequence, images[0], wait_trigger=False)

ro = RunningOrder(ActivationMethod.Immediate)
ro.add_frame_group(fg)

rep["reference"] = ro

## create repz
repz = RepertoireArchive(rep)

date = datetime.now()
timestamp = f"{date.year}{date.month:02d}{date.day:02d}T{date.hour:02d}{date.minute:02d}{date.second:02d}"
repz.save(f"packed_{timestamp}.repz11")
