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
import uuid
import urllib.request
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

TOP_LEVEL_DIR = os.path.abspath(os.curdir)


# test generic service-related functionality

os.environ["FOQUS_SERVICE_WORKING_DIR"] = "/tmp/foqus_test"
from .. import flowsheet

INSTANCE_USERDATA_JSON = b"""{"FOQUS-Update-Topic-Arn":"arn:aws:sns:us-east-1:387057575688:FOQUS-Update-Topic",
 "FOQUS-Message-Topic-Arn":"arn:aws:sns:us-east-1:387057575688:FOQUS-Message-Topic",
 "FOQUS-Job-Queue-Url":"https://sqs.us-east-1.amazonaws.com/387057575688/FOQUS-Gateway-FOQUSJobSubmitQueue-XPNWLF4Q38FD",
 "FOQUS-Simulation-Bucket-Name":"foqussimulationdevelopment1562016460",
 "FOQUS-DynamoDB-Table":"FOQUS_Table"
}"""


def test_floqus_aws_config():
    with patch("urllib.request.urlopen") as urllib.request.urlopen:
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
    tp = ("testuser", dict(Id=str(uuid.uuid4()), Simulation="test"))
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


class TestNode:
    # test some specific service-dependent node features

    @pytest.fixture(scope="function")
    def node(self):
        output = io.BytesIO(INSTANCE_USERDATA_JSON)
        flowsheet.FOQUSAWSConfig._inst = flowsheet.FOQUSAWSConfig()
        flowsheet.FOQUSAWSConfig._inst._d = json.loads(INSTANCE_USERDATA_JSON)
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

    def test_setSim_modelTurbine_xls(self, node):
        # manually add turbine model to test

        turbpath = os.path.abspath(
            os.path.join(
                TOP_LEVEL_DIR,
                "examples/tutorial_files/SimSinter/Tutorial_3/exceltest.json",
            )
        )
        print("dir: ", TOP_LEVEL_DIR)
        print(turbpath)

        with patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList:
            with patch(
                "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList"
            ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList:
                with patch(
                    "turbine.commands.turbine_simulation_script.main_update"
                ) as turbine.commands.turbine_simulation_script.main_update:
                    with patch(
                        "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig"
                    ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig:
                        app_list = ["ACM", "AspenPlus", "GProms", "Excel"]
                        foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList = MagicMock(
                            return_value=app_list
                        )
                        sim_list = [
                            "CO2_Compression_0715",
                            "exceltest",
                            "Flash_Example",
                            "Flash_Example_AP",
                        ]
                        foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList = MagicMock(
                            return_value=sim_list
                        )
                        mainupdate_val = True
                        turbine.commands.turbine_simulation_script.main_update = (
                            MagicMock(return_value=mainupdate_val)
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
                            simName="exceltest",
                            sinterConfigPath=os.path.normpath(turbpath),
                            update=True,
                            otherResources=[],
                        )

                        # set simulation
                        node.setSim(newModel="exceltest", newType=2)

    def test_runTurbineCalc_xls(self, node):
        # manually add turbine model to test

        turbpath = os.path.abspath(
            os.path.join(
                TOP_LEVEL_DIR,
                "examples/tutorial_files/SimSinter/Tutorial_3/exceltest.json",
            )
        )
        print("dir: ", TOP_LEVEL_DIR)
        print(turbpath)

        with patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList:
            with patch(
                "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList"
            ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList:
                with patch(
                    "turbine.commands.turbine_simulation_script.main_update"
                ) as turbine.commands.turbine_simulation_script.main_update:
                    with patch(
                        "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig"
                    ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig:
                        app_list = ["ACM", "AspenPlus", "GProms", "Excel"]
                        foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList = MagicMock(
                            return_value=app_list
                        )
                        sim_list = [
                            "CO2_Compression_0715",
                            "exceltest",
                            "Flash_Example",
                            "Flash_Example_AP",
                        ]
                        foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList = MagicMock(
                            return_value=sim_list
                        )
                        mainupdate_val = True
                        turbine.commands.turbine_simulation_script.main_update = (
                            MagicMock(return_value=mainupdate_val)
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
                            simName="exceltest",
                            sinterConfigPath=os.path.normpath(turbpath),
                            update=True,
                            otherResources=[],
                        )

                        # set simulation
                        node.setSim(newModel="exceltest", newType=2)
                        node.gr.turbConfig.dat = session()
                        node.runCalc()  # covers node.runTurbineCalc

    def test_setSim_modelTurbine_sim(self, node):
        # manually add turbine model to test

        turbpath = os.path.abspath(
            os.path.join(
                TOP_LEVEL_DIR,
                "examples/tutorial_files/SimSinter/Tutorial_2/Flash_Example_AP.json",
            )
        )
        print("dir: ", TOP_LEVEL_DIR)
        print(turbpath)

        with patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList:
            with patch(
                "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList"
            ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList:
                with patch(
                    "turbine.commands.turbine_simulation_script.main_update"
                ) as turbine.commands.turbine_simulation_script.main_update:
                    with patch(
                        "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig"
                    ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig:
                        app_list = ["ACM", "AspenPlus", "GProms", "Excel"]
                        foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList = MagicMock(
                            return_value=app_list
                        )
                        sim_list = [
                            "CO2_Compression_0715",
                            "exceltest",
                            "Flash_Example",
                            "Flash_Example_AP",
                        ]
                        foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList = MagicMock(
                            return_value=sim_list
                        )
                        mainupdate_val = True
                        turbine.commands.turbine_simulation_script.main_update = (
                            MagicMock(return_value=mainupdate_val)
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

    def test_runTurbineCalc_sim(self, node):
        # manually add turbine model to test

        turbpath = os.path.abspath(
            os.path.join(
                TOP_LEVEL_DIR,
                "examples/tutorial_files/SimSinter/Tutorial_2/Flash_Example_AP.json",
            )
        )
        print("dir: ", TOP_LEVEL_DIR)
        print(turbpath)

        with patch(
            "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList"
        ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList:
            with patch(
                "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList"
            ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList:
                with patch(
                    "turbine.commands.turbine_simulation_script.main_update"
                ) as turbine.commands.turbine_simulation_script.main_update:
                    with patch(
                        "foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig"
                    ) as foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSinterConfig:
                        app_list = ["ACM", "AspenPlus", "GProms", "Excel"]
                        foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getApplicationList = MagicMock(
                            return_value=app_list
                        )
                        sim_list = [
                            "CO2_Compression_0715",
                            "exceltest",
                            "Flash_Example",
                            "Flash_Example_AP",
                        ]
                        foqus_lib.framework.sim.turbineConfiguration.TurbineConfiguration.getSimulationList = MagicMock(
                            return_value=sim_list
                        )
                        mainupdate_val = True
                        turbine.commands.turbine_simulation_script.main_update = (
                            MagicMock(return_value=mainupdate_val)
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
                        node.gr.turbConfig.dat = session()
                        node.runCalc()  # covers node.runTurbineCalc
