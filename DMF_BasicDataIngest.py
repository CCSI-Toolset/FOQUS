#!/usr/bin/env python
import os
import sys
import argparse
import textwrap
from dmf_lib.basic_data.ingest import uploadFiles


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="DMF basic data ingester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        -------------------------------------------------
        The DMF basic data ingester is a standalone CLI
        that allows users to ingest data from Sorbent Fit into
        the CCSI Data Management Framework.
        -------------------------------------------------
        '''))
    parser.add_argument("src_folder", help="source files directory")
    parser.add_argument("-u", "--user", dest="user", help="username")
    parser.add_argument("-pw", "--password", dest="password", help="password")
    parser.add_argument("-i", "--index", dest="index", help="repo_index")
    parser.add_argument(
        "-c",
        "--confidence",
        dest="confidence",
        default='experimental',
        help="confidence of the files (experimental, testing, or production)")

    args = parser.parse_args()
    src_folder = args.src_folder

    if not os.path.isdir(src_folder):
        print "Error: Path " + src_folder + " does not exist, exiting."
        sys.exit(1)

    try:
        uploadFiles(
            src_folder, args.confidence,
            user=args.user, password=args.password,
            use_gateway=False,
            repo_index=args.index)

    except Exception, e:
        print "Terminating..."
