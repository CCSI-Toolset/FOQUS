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
from urllib.parse import urlparse
from shutil import copyfile
from botocore.stub import Stubber
import os

TOP_LEVEL_DIR = os.path.abspath(os.curdir)
os.environ["FOQUS_SERVICE_WORKING_DIR"] = "/tmp/foqus_test"
from .. import flowsheet

try:
    from unittest.mock import MagicMock, PropertyMock, patch
except ImportError:
    from mock import MagicMock, patch

INSTANCE_USERDATA_BIN = b"""{"FOQUS-Update-Topic-Arn":"arn:aws:sns:us-east-1:387057575688:FOQUS-Update-Topic",
 "FOQUS-Message-Topic-Arn":"arn:aws:sns:us-east-1:387057575688:FOQUS-Message-Topic",
 "FOQUS-Job-Queue-Url":"https://sqs.us-east-1.amazonaws.com/387057575688/FOQUS-Gateway-FOQUSJobSubmitQueue-XPNWLF4Q38FD",
 "FOQUS-Simulation-Bucket-Name":"foqussimulationdevelopment1562016460",
 "FOQUS-DynamoDB-Table":"FOQUS_Table",
 "FOQUS-User":"testuser",
 "FOQUS-Session-Bucket-Name":"testbucket"
}"""
INSTANCE_USERDATA_JSON = """{"FOQUS-Update-Topic-Arn":"arn:aws:sns:us-east-1:387057575688:FOQUS-Update-Topic",
 "FOQUS-Message-Topic-Arn":"arn:aws:sns:us-east-1:387057575688:FOQUS-Message-Topic",
 "FOQUS-Job-Queue-Url":"https://sqs.us-east-1.amazonaws.com/387057575688/FOQUS-Gateway-FOQUSJobSubmitQueue-XPNWLF4Q38FD",
 "FOQUS-Simulation-Bucket-Name":"foqussimulationdevelopment1562016460",
 "FOQUS-DynamoDB-Table":"FOQUS_Table",
 "FOQUS-User":"testuser",
 "FOQUS-Session-Bucket-Name":"testbucket"
}"""
TAGS_USERDATA_BIN = b"""FOQUS-Session-Bucket-Name FOQUS-Update-Topic-Arn FOQUS-Message-Topic-Arn FOQUS-Job-Queue-Url FOQUS-Simulation-Bucket-Name FOQUS-DynamoDB-Table FOQUS-User"""


def _url_open_side_effect(url):
    print("URL: " + url)
    up = urlparse(url)
    args = up.path.split("/")
    idx = args.index("meta-data")
    val = None
    if "region" in args:
        val = b"test-region"
    elif "instance-id" in args:
        val = b"i-testing"
    else:
        assert args[idx + 1] == "tags", "unexpected URL %s" % (url)
        assert args[idx + 2] == "instance", "unexpected URL %s" % (url)
        if len(args) == idx + 3:
            val = TAGS_USERDATA_BIN
        else:
            assert len(args) == idx + 4, "unexpect url path length %s" % (url)
            d = json.loads(INSTANCE_USERDATA_JSON)
            key = args[idx + 3]
            assert key in d, "Missing Key in %s, instance-data %s" % (url, str(args))
            val = d[key].encode("ascii")
    return io.BytesIO(val)


@patch("urllib.request.urlopen")
def test_floqus_aws_config(mock_urlopen):
    # output = io.BytesIO(INSTANCE_USERDATA_JSON)
    # urllib.request.urlopen = MagicMock(return_value=output)
    mock_urlopen.side_effect = _url_open_side_effect
    config = flowsheet.FOQUSAWSConfig.get_instance()


@patch("urllib.request.urlopen")
def test_flowsheet_control(mock_urlopen):
    # output = io.BytesIO(INSTANCE_USERDATA_JSON)
    # flowsheet.FOQUSAWSConfig._inst = flowsheet.FOQUSAWSConfig()
    # flowsheet.FOQUSAWSConfig._inst._d = json.loads(INSTANCE_USERDATA_JSON)
    mock_urlopen.side_effect = _url_open_side_effect
    fc = flowsheet.FlowsheetControl()


def mock_boto_client(*args, **kw):
    class MockCli:
        def put_metric_data(self, **kw):
            print("IGNORE %s" % kw)

    return MockCli()


@patch("boto3.client")
@patch("urllib.request.urlopen")
def test_flowsheet_control_run(mock_urlopen, mock_boto):
    mock_urlopen.side_effect = _url_open_side_effect
    mock_boto.side_effect = mock_boto_client
    flowsheet.TurbineLiteDB.consumer_register = MagicMock(return_value=None)
    flowsheet.TurbineLiteDB.add_message = MagicMock(return_value=None)
    flowsheet.TurbineLiteDB.job_change_status = MagicMock(return_value=None)
    flowsheet.TurbineLiteDB.consumer_keepalive = MagicMock(return_value=None)
    # pop_job:  downloads simulation file into working dir
    tp = (
        "testuser",
        dict(Id=str(uuid.uuid4()), Simulation="test", sessionid=str(uuid.uuid4())),
    )
    flowsheet.FlowsheetControl.pop_job = MagicMock(return_value=tp)
    orig_simulation_file_path = os.path.abspath(
        os.path.join(
            TOP_LEVEL_DIR,
            "examples/tutorial_files/Flowsheets/Tutorial_1/Simple_flow.foqus",
        )
    )
    sfile, rfile, vfile, ofile = flowsheet.getfilenames(tp[1]["Id"])

    copyfile(orig_simulation_file_path, sfile)
    with open(vfile, "w") as fd:
        fd.write("{}")

    flowsheet.FlowsheetControl._delete_sqs_job = MagicMock(return_value=None)

    fc = flowsheet.FlowsheetControl()
    stubber = Stubber(fc._dynamodb)
    fc._dynamodb = stubber
    # _describe_table_response = {}
    # expected_params = dict(TableName=fc._dynamodb_table_name)
    # stubber.add_response('describe_table', _describe_table_response, expected_params)
    # stubber.activate()
    # stubber doesn't WORK.
    stubber.describe_table = MagicMock(return_value=None)
    stubber.get_item = MagicMock(
        return_value=dict(Item={"Id": "hi", "Simulation": "test"})
    )

    def _run_foqus(self, db, job_desc):
        fc.stop()

    flowsheet.FlowsheetControl.run_foqus = _run_foqus
    fc.run()
