import glob
from io import StringIO
import os
from pathlib import Path
from zipfile import ZipFile

seq_path = "S:/Andy/48071 HHMI 50ms.seq11"

image_dir = "C:/Users/Andy/Desktop/NA0.64_na0.45"
image_list = glob.glob(os.path.join(image_dir, "*.bmp"))

# sort by tc
image_list.sort(key=lambda x: float(Path(x).stem.split("_")[-1][2:]))

rep = StringIO()
# write sequence
rep.write("SEQUENCES\n")
seq_file = os.path.basename(seq_path)
rep.write(f'A "{seq_file}"')
rep.write("SEQUENCES_END\n")

rep.write("\n")

# write images
rep.write("IMAGES\n")
for image_path in image_list:
    image_file = os.path.basename(image_path)
    rep.write(f'1 "{image_file}"\n')
rep.write("IMAGES_END\n")

rep.write("\n")

# write RO
rep.write('DEFAULT "RO1"\n')
rep.write("[HWA\n")
rep.write("<")
rep.write("t")
for i, _ in enumerate(image_list):
    rep.write(f"(A,{i}) ")
rep.write(">\n")
rep.write("{")
for i, _ in enumerate(image_list):
    rep.write(f"(A,{i}) ")
rep.write("}\n")
rep.write("]\n")

# create repz
with ZipFile("output.repz11", "w") as repz:
    repz.writestr("repertoire.rep", rep.getvalue())
    repz.write(seq_path, arcname=os.path.basename(seq_path))
    for image_path in image_list:
        repz.write(image_path, arcname=os.path.basename(image_path))
