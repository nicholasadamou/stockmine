#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""logs.py - logging variables for how stockmine displays logs.

See README.md or https://github.com/nicholasadamou/stockmine
for more information.

Copyright (C) Nicholas Adamou 2019
stockmine is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

WARNING = f"[{YELLOW}!{RESET}]"
ERROR = f"[{RED}X{RESET}]"
OK = f"[{GREEN}+{RESET}]"
SUCCESS = f"[{GREEN}✔{RESET}]"
