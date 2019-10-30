"""flowsheet_control_test.py

* This contains tests for results instance

Joshua Boverhof, Lawrence Berekeley National Lab, 2018
John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
import json
import logging
import time
from .. import flowsheet
import urllib.request
try:
    from unittest.mock import MagicMock,patch
except ImportError:
    from mock import MagicMock,patch


def test_flowsheet_control():
    flowsheet.FlowsheetControl._set_working_directory("/tmp/foqus_test/")
    #fc = flowsheet.FlowsheetControl()
