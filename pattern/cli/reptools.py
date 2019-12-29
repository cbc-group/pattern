import glob
import logging
import os

import click
import coloredlogs

from pattern.fourthdd import RepertoireArchive


@click.command()
@click.argument("rep_file", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option(
    "-s", "--seq_dir", type=click.Path(exists=True, file_okay=False, readable=True)
)
@click.option(
    "-i", "--img_dir", type=click.Path(exists=True, file_okay=False, readable=True)
)
@click.option("-c", "--repz_file", type=click.Path(dir_okay=False, readable=True))
@click.option("-o", "--overwrite", is_flag=True)
def repbuild(rep_file, seq_dir, img_dir, repz_file, overwrite):
    repz = RepertoireArchive(rep_file)

    repz.sequences = glob.glob(os.path.join(seq_dir, "*.seq*"))
    repz.images = glob.glob(os.path.join(seq_dir, "*.bmp"))

    RepertoireArchive.dump(repz_file, repz)
