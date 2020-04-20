#!/usr/env python3
# Reference: https://docs.python-guide.org/writing/structure/

import os
import sys

# Top directory for cumulus git repository
topdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', ))

# Add module to path
sys.path.insert(0, topdir)

from core import (
    config,
    helpers
)

