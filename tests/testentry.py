#!/usr/bin/env python3
import os
import sys

from qdep.internal.cli import main

if __name__ == '__main__':
	print(os.environ["PYTHONPATH"])
	sys.exit(main())
