"""
Minimal setup.py to simplify project setup.
"""
from setuptools import find_packages, setup

setup(
    name="pattern",
    version="0.1",
    description="",
    author="Liu, Yen-Ting",
    author_email="ytliu@gate.sinica.edu.tw",
    license="Apache 2.0",
    packages=find_packages(),
    package_data={"": ["data/*"]},
    install_requires=[
        "click",
        "coloredlogs",
        "imageio",
        "matplotlib",
        "numpy",
        'pyqtgraph>=0.11.0rc0',
        'pyside2==5.12.0'
        "scipy",
        "tqdm",
    ],
    zip_safe=True,
    extras_require={},
    entry_points={"console_scripts": ["repbuild=pattern.cli.reptools:repbuild"]},
)
