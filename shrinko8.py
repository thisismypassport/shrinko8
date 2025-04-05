#!/usr/bin/env python3
from shrinko import create_main
from pico_defs import Language
import sys

main = create_main(Language.pico8)

if __name__ == "__main__":
    sys.exit(main())
