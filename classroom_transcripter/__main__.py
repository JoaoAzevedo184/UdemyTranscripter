"""Permite execução via `python -m udemy_transcripter`."""

import sys

from .cli import main

sys.exit(main())