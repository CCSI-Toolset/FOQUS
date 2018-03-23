"""version.py
* This just contains some version and legal info for FOQUS

John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""

import argparse, sys

version = "2017.12.0.0" #Build in Jenkins inserts build number
copyright = "See LICENSE.md for license and copyright details."
license = "See LICENSE.md for license and copyright details."
author = "CCSI FOQUS Team"
support = "Support ccsi-support@acceleratecarboncapture.org"
webpage = "http://www.acceleratecarboncapture.org/"
maintainer = "John Eslick"
maintainer_email = "john.eslick@netl.doe.gov"

if __name__ == '__main__':
    '''
        This just returns the requested information for use in whatever
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        help = "Print version",
        action="store_true")
    parser.add_argument(
        "--author",
        help = "Print author",
        action="store_true")
    parser.add_argument(
        "--copyright",
        help = "Print copyright",
        action="store_true")
    parser.add_argument(
        "--license",
        help = "Print license short statement (not full license)",
        action="store_true")
    parser.add_argument(
        "--support",
        help = "Print support information",
        action="store_true")
    parser.add_argument(
        "--webpage",
        help = "Print web page ",
        action="store_true")
    args = parser.parse_args()
    if args.version:
        print version
    if args.copyright:
        print copyright
    if args.license:
        print license
    if args.support:
        print support
    if args.webpage:
        print webpage
    if len(sys.argv) <= 1:
        print version
