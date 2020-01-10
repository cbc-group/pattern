from datetime import datetime
import glob
from io import StringIO
import os
from pathlib import Path
from zipfile import ZipFile

seq_name = "48071 HHMI 50ms"
seq_path = os.path.join("Sequences", seq_name, f"{seq_name}.seq11")

image_dir = "S:/Andy/NA0.22944_na0.16134_45b"
image_list = glob.glob(os.path.join(image_dir, "*.bmp"))

# sort by tc
image_list.sort(key=lambda x: float(Path(x).stem.split("_")[-2][2:]))
# sort by na
# image_list.sort(key=lambda x: float(Path(x).stem.split("_")[3][2:]))

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
n_repeat = 2
rep.write('DEFAULT "Continuous"\n')
rep.write("[HWA s\n")
rep.write("<")
rep.write("t")
for i, _ in enumerate(image_list):
    for _ in range(n_repeat):
        rep.write(f"(A,{i}) ")
rep.write(">\n")
rep.write("{")
for i, _ in enumerate(image_list):
    for _ in range(n_repeat):
        rep.write(f"(A,{i}) ")
rep.write("}\n")
rep.write("]\n")

rep.write('"Standard"\n')
rep.write("[HWA s\n")
rep.write("<")
rep.write("t")
for _ in range(n_repeat):
    rep.write("(A,0) ")
rep.write(">\n")
rep.write("{")
for _ in range(n_repeat):
    rep.write("(A,0) ")
rep.write("}\n")
rep.write("]\n")

# create repz
date = datetime.now()
timestamp = f"{date.year}{date.month:02d}{date.day:02d}T{date.hour:02d}{date.minute:02d}{date.second:02d}"
with ZipFile(f"packed_{timestamp}.repz11", "w") as repz:
    repz.writestr("repertoire.rep", rep.getvalue())
    repz.write(seq_path, arcname=os.path.basename(seq_path))
    for image_path in image_list:
        repz.write(image_path, arcname=os.path.basename(image_path))
