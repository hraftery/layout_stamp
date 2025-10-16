#!/usr/bin/env python3

import sys
import layout_stamp

# plugin.json doesn't seem to support passing arguments in "entrypoint"
# so use this dedicated script file and function call instead.
layout_stamp.main(sys.argv + ['paste'])
