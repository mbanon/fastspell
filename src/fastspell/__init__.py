#!/usr/bin/env python
from importlib.metadata import version

name="fastspell"
__version__ = version(name)

from .fastspell import FastSpell
