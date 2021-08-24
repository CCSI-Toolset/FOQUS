###############################################################################
# FOQUS Copyright (c) 2012 - 2021, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#
###############################################################################
"""flowsheet_control_test.py

* This contains tests for results instance

Joshua Boverhof, Lawrence Berekeley National Lab, 2018
John Eslick, Carnegie Mellon University, 2014
"""
import io
import json
import logging
import time
import uuid
import urllib.request
from shutil import copyfile
from botocore.stub import Stubber
import os
TOP_LEVEL_DIR = os.path.abspath(os.curdir)
os.environ['FOQUS_SERVICE_WORKING_DIR'] = '/tmp/foqus_test'
from .. import flowsheet
try:
    from unittest.mock import MagicMock,PropertyMock,patch
except ImportError:
    from mock import MagicMock,patch

INSTANCE_USERDATA_JSON = b'''{"FOQUS-Update-Topic-Arn":"arn:aws:sns:us-east-1:387057575688:FOQUS-Update-Topic",
 "FOQUS-Message-Topic-Arn":"arn:aws:sns:us-east-1:387057575688:FOQUS-Message-Topic",
 "FOQUS-Job-Queue-Url":"https://sqs.us-east-1.amazonaws.com/387057575688/FOQUS-Gateway-FOQUSJobSubmitQueue-XPNWLF4Q38FD",
 "FOQUS-Simulation-Bucket-Name":"foqussimulationdevelopment1562016460",
 "FOQUS-DynamoDB-Table":"FOQUS_Table"
}'''

def test_floqus_aws_config():
    output = io.BytesIO(INSTANCE_USERDATA_JSON)
    urllib.request.urlopen = MagicMock(return_value=output)
    config = flowsheet.FOQUSAWSConfig()
    config.get_instance()

def test_flowsheet_control():
    output = io.BytesIO(INSTANCE_USERDATA_JSON)
    flowsheet.FOQUSAWSConfig._inst = flowsheet.FOQUSAWSConfig()
    flowsheet.FOQUSAWSConfig._inst._d = json.loads(INSTANCE_USERDATA_JSON)
    fc = flowsheet.FlowsheetControl()


def test_flowsheet_control_run():
    output = io.BytesIO(INSTANCE_USERDATA_JSON)
    flowsheet.FOQUSAWSConfig._inst = flowsheet.FOQUSAWSConfig()
    flowsheet.FOQUSAWSConfig._inst._d = json.loads(INSTANCE_USERDATA_JSON)
    flowsheet.TurbineLiteDB.consumer_register = MagicMock(return_value=None)
    flowsheet.TurbineLiteDB.add_message = MagicMock(return_value=None)
    flowsheet.TurbineLiteDB.job_change_status = MagicMock(return_value=None)
    flowsheet.TurbineLiteDB.consumer_keepalive = MagicMock(return_value=None)
    # pop_job:  downloads simulation file into working dir
    tp = ('testuser', dict(Id=str(uuid.uuid4()), Simulation='test'))
    flowsheet.FlowsheetControl.pop_job = MagicMock(return_value=tp)
    orig_simulation_file_path = os.path.abspath(
        os.path.join(TOP_LEVEL_DIR,
            'examples/tutorial_files/Flowsheets/Tutorial_1/Simple_flow.foqus'
        )
    )
    sfile,rfile,vfile,ofile = flowsheet.getfilenames(tp[1]['Id'])

    copyfile(orig_simulation_file_path, sfile)
    with open(vfile, 'w') as fd:
        fd.write("{}")

    flowsheet.FlowsheetControl._delete_sqs_job = MagicMock(return_value=None)

    fc = flowsheet.FlowsheetControl()
    stubber = Stubber(fc._dynamodb)
    fc._dynamodb = stubber
    #_describe_table_response = {}
    #expected_params = dict(TableName=fc._dynamodb_table_name)
    #stubber.add_response('describe_table', _describe_table_response, expected_params)
    #stubber.activate()
    # stubber doesn't WORK.
    stubber.describe_table = MagicMock(return_value=None)
    stubber.get_item = MagicMock(return_value=dict(
        Item={'Id':'hi', 'Simulation':'test'}))

    def _run_foqus(self, db, job_desc):
        fc.stop()

    flowsheet.FlowsheetControl.run_foqus = _run_foqus
    fc.run()
