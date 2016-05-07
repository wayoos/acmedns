#!/usr/bin/env python
#  -*- encoding: utf-8 -*-
#
# Copyright (c) 2016 Wayoos
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import logging
import argparse
import textwrap
from acmedns.config import ConfigurationManager
from acmedns.domain import DomainManager


def main(argv):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            This script automates the process of getting a signed TLS certificate from
            Let's Encrypt using the ACME protocol. It will need to be run on your server
            and have access to your private account key.

            ===Example Usage===
            python acmedns.py --config acmedns.conf
            ===================

            """)
    )
    parser.add_argument("--config", required=True, help="path to your acmedns config file")
    parser.add_argument("--log", default='info', help="define log level")
    args = parser.parse_args(argv)
    numeric_level = getattr(logging, args.log.upper(), None)
    logging.basicConfig(level=numeric_level)

    config_mngt = ConfigurationManager.from_filename(args.config)
    domain_mngt = DomainManager.from_config(config_mngt)
    domain_mngt.sign_all()

if __name__ == "__main__":
    main(sys.argv[1:])
