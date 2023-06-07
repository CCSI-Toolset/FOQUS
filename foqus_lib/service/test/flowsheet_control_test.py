#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
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
#################################################################################
"""flowsheet_control_test.py

* This contains tests for results instance

Joshua Boverhof, Lawrence Berekeley National Lab, 2018
John Eslick, Carnegie Mellon University, 2014
"""
import io
import json
import uuid
import urllib.request
from urllib.parse import urlparse
from shutil import copyfile
from botocore.stub import Stubber
import os

import pytest
import foqus_lib
import turbine
from foqus_lib.framework.graph.graph import Graph
from foqus_lib.framework.graph.node import Node
from foqus_lib.framework.sim.turbineConfiguration import TurbineConfiguration
from foqus_lib.framework.session.session import session

try:
    from unittest.mock import MagicMock, PropertyMock, patch
except ImportError:
    from mock import MagicMock, patch


# test generic service-related functionality

os.environ["FOQUS_SERVICE_WORKING_DIR"] = "/tmp/foqus_test"
from .. import flowsheet

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
    # output = io.BytesIO(INSTANCE_USERDATA_BIN)
    # urllib.request.urlopen = MagicMock(return_value=output)
    mock_urlopen.side_effect = _url_open_side_effect
    config = flowsheet.FOQUSAWSConfig.get_instance()


@patch("urllib.request.urlopen")
def test_flowsheet_control(mock_urlopen):
    # output = io.BytesIO(INSTANCE_USERDATA_BIN)
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
def test_flowsheet_control_run(mock_urlopen, mock_boto, foqus_examples_dir):
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
            foqus_examples_dir,
            "tutorial_files/Flowsheets/Tutorial_1/Simple_flow.foqus",
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


@patch("boto3.client")
@patch("urllib.request.urlopen")
class TestNode:
    # test some specific service-dependent node features

    @pytest.fixture(scope="function")
    def node(self, mock_urlopen):
        mock_urlopen.side_effect = _url_open_side_effect
        # mock_boto.side_effect = mock_boto_client
        # flowsheet.FOQUSAWSConfig._inst = flowsheet.FOQUSAWSConfig()
        # flowsheet.FOQUSAWSConfig._inst._d = json.loads(INSTANCE_USERDATA_JSON)
        flowsheet.TurbineLiteDB.consumer_register = MagicMock(return_value=None)
        flowsheet.TurbineLiteDB.add_message = MagicMock(return_value=None)
        flowsheet.TurbineLiteDB.job_change_status = MagicMock(return_value=None)
        flowsheet.TurbineLiteDB.consumer_keepalive = MagicMock(return_value=None)
        # pop_job:  downloads simulation file into working dir
        tp = ("testuser", dict(Id=str(uuid.uuid4()), Simulation="test"))
        flowsheet.FlowsheetControl.pop_job = MagicMock(return_value=tp)

        flowsheet.FlowsheetControl._delete_sqs_job = MagicMock(return_value=None)

        fc = flowsheet.FlowsheetControl()
        print("fc: ", fc)
        # build graph, add node and return node
        gr = Graph()
        gr.addNode("testnode")
        n = Node(parent=gr, name="testnode")

        return n

    def test_setSim_modelTurbine_xls(self, node, mock_urlopen, foqus_examples_dir):
        # manually add turbine model to test
        turbpath = (
            foqus_examples_dir / "tutorial_files/SimSinter/Tutorial_3/exceltest.json"
        ).resolve()
        print(turbpath)

        with patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList, patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList, patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig, patch(
            "turbine.commands.turbine_simulation_script.main_update"
        ) as turbine.commands.turbine_simulation_script.main_update:

            app_list = ["ACM", "AspenPlus", "Excel"]
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList = MagicMock(
                return_value=app_list
            )

            sim_list = ["exceltest", "Flash_Example_AP"]
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList = MagicMock(
                return_value=sim_list
            )

            mainupdate_val = True
            turbine.commands.turbine_simulation_script.main_update = MagicMock(
                return_value=mainupdate_val
            )

            sinterconfig_json = json.loads(turbpath.read_text())
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig = MagicMock(
                return_value=sinterconfig_json
            )

            # create config block and upload model files to Turbine
            node.gr.turbConfig = TurbineConfiguration()
            node.gr.turbConfig.writeConfig(overwrite=True)
            node.gr.turbConfig.uploadSimulation(
                simName="exceltest",
                sinterConfigPath=os.fspath(turbpath),
                update=True,
                otherResources=[],
            )

            # set simulation
            node.setSim(newModel="exceltest", newType=2)

    def test_runTurbineCalc_xls(self, node, mock_urlopen, foqus_examples_dir):
        # manually add turbine model to test
        turbpath = (
            foqus_examples_dir / "tutorial_files/SimSinter/Tutorial_3/exceltest.json"
        ).resolve()
        print(turbpath)

        with patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList, patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList, patch(
            "turbine.commands.turbine_simulation_script.main_update"
        ) as turbine.commands.turbine_simulation_script.main_update, patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig, patch(
            "turbine.commands.turbine_simulation_script.main_list"
        ) as turbine.commands.turbine_simulation_script.main_list:

            app_list = ["Excel"]
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList = MagicMock(
                return_value=app_list
            )

            sim_list = ["exceltest"]
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList = MagicMock(
                return_value=sim_list
            )

            mainupdate_val = True
            turbine.commands.turbine_simulation_script.main_update = MagicMock(
                return_value=mainupdate_val
            )

            f = open(turbpath, "r")
            sinterconfig_json = json.loads(f.read())
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig = MagicMock(
                return_value=sinterconfig_json
            )
            f.close()

            mainlist_list = [
                {
                    "Application": "Excel",
                    "Id": "31054748-f627-45ab-a3eb-d96131635acc",
                    "Name": "exceltest",
                    "StagedInputs": [
                        {
                            "Id": "3779977f-2f2d-48c8-a5fc-1290eed8f868",
                            "MD5Sum": "B559FFB87D9A122578A550E45DE5E06E13E59C3A",
                            "Name": "spreadsheet",
                        },
                        {
                            "Id": "e198ad4e-0003-4373-917b-9f24b2fb78ce",
                            "MD5Sum": "A04FC0B4B4DAD3EFDBC50583686EF9B27C4E269F",
                            "Name": "configuration",
                        },
                    ],
                },
            ]
            turbine.commands.turbine_simulation_script.main_list = MagicMock(
                return_value=mainlist_list
            )

            # create config block and upload model files to Turbine
            node.gr.turbConfig = TurbineConfiguration()
            node.gr.turbConfig.writeConfig(overwrite=True)
            node.gr.turbConfig.uploadSimulation(
                simName="exceltest",
                sinterConfigPath=os.path.normpath(turbpath),
                update=True,
                otherResources=[],
            )

            # set simulation
            node.setSim(newModel="exceltest", newType=2)
            node.gr.turbConfig.dat = session(useCurrentWorkingDir=True)
            node.options["Override Turbine Configuration"].value = None
            node.runCalc()  # covers node.runTurbineCalc

    def test_setSim_modelTurbine_sim(self, node, mock_urlopen, foqus_examples_dir):
        # manually add turbine model to test
        turbpath = (
            foqus_examples_dir
            / "tutorial_files/SimSinter/Tutorial_2/Flash_Example_AP.json"
        ).resolve()
        print(turbpath)

        with patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList, patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList, patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig, patch(
            "turbine.commands.turbine_simulation_script.main_update"
        ) as turbine.commands.turbine_simulation_script.main_update:

            app_list = ["ACM", "AspenPlus"]
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList = MagicMock(
                return_value=app_list
            )

            sim_list = ["Flash_Example_AP"]
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList = MagicMock(
                return_value=sim_list
            )

            mainupdate_val = True
            turbine.commands.turbine_simulation_script.main_update = MagicMock(
                return_value=mainupdate_val
            )

            f = open(turbpath, "r")
            sinterconfig_json = json.loads(f.read())
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig = MagicMock(
                return_value=sinterconfig_json
            )
            f.close()

            # create config block and upload model files to Turbine
            node.gr.turbConfig = TurbineConfiguration()
            node.gr.turbConfig.writeConfig(overwrite=True)
            node.gr.turbConfig.uploadSimulation(
                simName="Flash_Example_AP",
                sinterConfigPath=os.path.normpath(turbpath),
                update=True,
                otherResources=[],
            )

            # set simulation
            node.setSim(newModel="Flash_Example_AP", newType=2)

    def test_runTurbineCalc_sim(self, node, mock_urlopen, foqus_examples_dir):
        # manually add turbine model to test
        turbpath = (
            foqus_examples_dir
            / "tutorial_files/SimSinter/Tutorial_2/Flash_Example_AP.json"
        ).resolve()
        print(turbpath)

        with patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList, patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList, patch(
            "turbine.commands.turbine_simulation_script.main_update"
        ) as turbine.commands.turbine_simulation_script.main_update, patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig, patch(
            "turbine.commands.turbine_simulation_script.main_list"
        ) as turbine.commands.turbine_simulation_script.main_list:

            app_list = ["ACM", "AspenPlus"]
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList = MagicMock(
                return_value=app_list
            )

            sim_list = ["Flash_Example_AP"]
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList = MagicMock(
                return_value=sim_list
            )

            mainupdate_val = True
            turbine.commands.turbine_simulation_script.main_update = MagicMock(
                return_value=mainupdate_val
            )

            f = open(turbpath, "r")
            sinterconfig_json = json.loads(f.read())
            foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig = MagicMock(
                return_value=sinterconfig_json
            )
            f.close()

            mainlist_list = [
                {
                    "Application": "AspenPlus",
                    "Id": "389d6312-ab13-4b20-88cb-f7bb96c013e3",
                    "Name": "Flash_Example_AP",
                    "StagedInputs": [
                        {
                            "Id": "0f0b29bd-a249-4fc2-86f7-2c4570f9201e",
                            "MD5Sum": "CF4EEE41C46D28764CCA30932B1C0722BCD01A93",
                            "Name": "Flash_Example.bkp",
                        },
                        {
                            "Id": "76b8513d-d847-4902-b67e-7760973b7b42",
                            "MD5Sum": "",
                            "Name": "aspenfile",
                        },
                        {
                            "Id": "ca123730-134f-415a-8b30-c1955320acb3",
                            "MD5Sum": "A59CFCA2624EDC073623649E3BF98221D82DDCF0",
                            "Name": "configuration",
                        },
                    ],
                },
            ]
            turbine.commands.turbine_simulation_script.main_list = MagicMock(
                return_value=mainlist_list
            )

            # create config block and upload model files to Turbine
            node.gr.turbConfig = TurbineConfiguration()
            node.gr.turbConfig.writeConfig(overwrite=True)
            node.gr.turbConfig.uploadSimulation(
                simName="Flash_Example_AP",
                sinterConfigPath=os.path.normpath(turbpath),
                update=True,
                otherResources=[],
            )

            # set simulation
            node.setSim(newModel="Flash_Example_AP", newType=2)
            node.gr.turbConfig.dat = session(useCurrentWorkingDir=True)
            node.options["Override Turbine Configuration"].value = None
            node.runCalc()  # covers node.runTurbineCalc
