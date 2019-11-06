"""flowsheet_control_test.py

* This contains tests for results instance

Joshua Boverhof, Lawrence Berekeley National Lab, 2018
John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
import io
import json
import logging
import time
import uuid
from .. import flowsheet
import urllib.request
from botocore.stub import Stubber
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
    flowsheet.FlowsheetControl.pop_job = MagicMock(return_value=('testuser', dict(Id=str(uuid.uuid4()))))
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
    stubber.get_item = MagicMock(return_value=dict(Item={}))

    fc._stop = True

    fc.run()
