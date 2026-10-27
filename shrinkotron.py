#!/usr/bin/env python3
"""Script to run the shrinko command line in shrinkotron (picotron) mode. The actual command line logic is in run_shrinko"""
import os, sys
if __package__ not in (None, ""):
    sys.path.insert(0, os.path.dirname(__file__))

from run_shrinko import create_main
from pico_defs import Language

main = create_main(Language.picotron)

if __name__ == "__main__":
    sys.exit(main())
