#!/usr/bin/env python

import setuptools
import subprocess
import os.path

if __name__=="__main__":
    with open("README.md", "r") as fh:
        long_description = fh.read()
    with open("requirements.txt") as rf:
        requirements = rf.read().splitlines()

    setuptools.setup(
        name="fastspell",
        version="0.5",
        install_requires=requirements,
        license="GNU General Public License v3.0",
        author="Prompsit Language Engineering",
        author_email="info@prompsit.com",
        description="Targetted language identifier, based on FastText and Hunspell.",
        maintainer="Marta Bañon",
        maintainer_email="mbanon@prompsit.com",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/mbanon/fastspell",
        packages=["fastspell"],
        package_data={
            'fastspell': ['config/*.yaml', '../requirements.txt']
        },
        classifiers=[
            "Environment :: Console",
            "Intended Audience :: Science/Research",
            "Programming Language :: Python :: 3.7",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: POSIX :: Linux",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "Topic :: Text Processing :: Linguistic",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Text Processing :: Filters"
        ],
        project_urls={
            "FastSpell on GitHub": "https://github.com/mbanon/fastspell",
            "Prompsit Language Engineering": "http://www.prompsit.com",
            "Paracrawl": "https://paracrawl.eu/"
             },
        entry_points={
            "console_scripts": [
                "fastspell=fastspell.fastspell:main",
                "fastspell-download=fastspell.fastspell_download:main",
            ],
        }
    )
