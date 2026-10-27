#!/usr/bin/env python3
"""Script to run the shrinko command line in shrinko8 (pico8) mode. The actual command line logic is in run_shrinko"""
import os, sys
if __package__ not in (None, ""):
    sys.path.insert(0, os.path.dirname(__file__))

from run_shrinko import create_main
from pico_defs import Language

main = create_main(Language.pico8)

if __name__ == "__main__":
    sys.exit(main())
