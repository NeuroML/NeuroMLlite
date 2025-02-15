from setuptools import setup

version = ""
for aline in open("neuromllite/__init__.py"):
    if "__version__ =" in aline:
        version = aline.split('"')[1]

setup(
    name="neuromllite",
    version=version,
    author="Padraig Gleeson",
    author_email="p.gleeson@gmail.com",
    packages=["neuromllite", "neuromllite.sweep", "neuromllite.gui"],
    entry_points={
        "console_scripts": ["nmllite-ui            = neuromllite.gui.NMLliteUI:main"]
    },
    url="https://github.com/NeuroML/NeuroMLlite",
    license="LICENSE.lesser",
    description="A common JSON/YAML based format for compact network specification, closely tied to NeuroML v2",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "libNeuroML>=0.5.1",
        "pyyaml",
        "numpy<2.0.0",
        "tables",
        "h5py",
        "modelspec>=0.2.6",
        "ppft"
    ],
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
    ],
)
