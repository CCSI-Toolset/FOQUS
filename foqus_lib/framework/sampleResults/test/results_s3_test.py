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
"""results_s3_test.py

* This contains tests for results instance

Joshua Boverhof, Lawrence Berekeley National Lab, 2018
John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
import json
import logging
import time
from .. import results
from ...graph.graph import Graph

try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch


def test_results_empty():
    """Paging results from session results generator
    solTime -- Amount of time used to solve graph outputs
    """
    sd = {
        "solTime": None,
        "input": dict(),
        "output": dict(),
        "graphError": None,
        "nodeError": {},
        "nodeSettings": {},
        "turbineMessages": {},
    }
    obj = results.Results()
    setName = "s3test"
    name = "whatever"
    obj.addFromSavedValues(setName, name, valDict=sd)

    assert 5 == obj.count_cols()


def test_add_result_single():
    """ """
    obj = results.Results()
    setName = "s3test"
    name = "whatever"
    # sd = self.singleRun.res[0]
    sd = {
        "resub": 0,
        "nodeError": {},
        "session": "9f4def1c-d033-4761-9e8d-7ae979d230ae",
        "turbineMessages": {},
        "graphError": -3,
        "Id": "08e6bf2d-e6e2-4e75-8ce2-8e86a6a0db83",
    }
    obj.add_result(
        set_name="Single_runs", result_name="single_{}".format(0), time=None, sd=sd
    )

    assert 4 == obj.count_cols()


def test_results_session_broke_result_page():
    """Paging results from session results generator

    graph.solveListValTurbine
    """
    _log = logging.getLogger(__name__)
    session_id = "9f4def1c-d033-4761-9e8d-7ae979d230ae"
    result_id = "03ce8184-3f2f-4445-9d4c-7141a28662e8"
    fname = (
        "cloud/aws/test/data/s3/foqus-sessions/anonymous/%(session)s/%(result)s/%(page)s"
        % dict(session=session_id, result=result_id, page="1.json")
    )

    with open(fname) as fd:
        page = json.load(fd)
        assert 1 == len(page)

    # obj = results.Results()
    setName = "s3test"
    name = "whatever"
    jids = list(map(lambda i: i["Id"], page))
    g = Graph()
    # g.solveListValTurbineCreateSession = MagicMock(return_value=session_id)
    g.solveListValTurbineGetGenerator = MagicMock(return_value=result_id)
    g.turbConfig.createSession = MagicMock(return_value=session_id)
    g.turbConfig.deleteCompletedJobsGen = MagicMock(return_value=None)
    g.turbConfig.createJobsInSession = MagicMock(return_value=jids)
    g.turbConfig.startSession = MagicMock(return_value=jids)
    g.solveListValTurbineGetGeneratorPage = MagicMock(return_value=1)
    g.solveListValTurbineGeneratorReadPage = MagicMock(return_value=page)
    g.resubMax = 0  # NOTE: SHOULD BE in constructor
    g.turbchkfreq = 0
    g.status = dict(unfinished=len(jids), finished=0, success=0)
    g.res_re = [0] * 1  # NOTE: No idea what this is for..
    g.res = [None] * 1  # NOTE:??? HOLDER???  runListAsThread
    g.res_fin = [-1] * 1  # NOTE: runListAsThread

    g.solveListValTurbine(valueList=[jids], maxSend=20, sid=session_id, jobIds=jids)

    assert g.status["success"] == 0
    assert g.status["unfinished"] == 0
    assert g.status["error"] == 1
    assert len(g.res) == 1
    assert set(map(lambda i: i["Id"], g.res)) == set(jids)
    i = g.res[0]
    assert i["session"] == session_id
    assert i["graphError"] == -3


def test_results_session_result_page_1():
    """Paging results from session results generator

    graph.solveListValTurbine
    """
    _log = logging.getLogger(__name__)
    session_id = "6f85fc45-6044-478a-b56e-ac5f820eb861"
    result_id = "b6c71dc1-5c93-4526-99ef-07d6af0ba59f"
    fname = (
        "cloud/aws/test/data/s3/foqus-sessions/anonymous/%(session)s/%(result)s/%(page)s"
        % dict(session=session_id, result=result_id, page="1.json")
    )

    with open(fname) as fd:
        page = json.load(fd)
        assert 3 == len(page)

    # obj = results.Results()
    setName = "s3test"
    name = "whatever"
    jids = [i["Id"] for i in page]
    g = Graph()
    # g.solveListValTurbineCreateSession = MagicMock(return_value=session_id)
    g.solveListValTurbineGetGenerator = MagicMock(return_value=result_id)
    g.turbConfig.createSession = MagicMock(return_value=session_id)
    g.turbConfig.deleteCompletedJobsGen = MagicMock(return_value=None)
    g.turbConfig.createJobsInSession = MagicMock(return_value=jids)
    g.turbConfig.startSession = MagicMock(return_value=jids)
    g.solveListValTurbineGetGeneratorPage = MagicMock(return_value=1)
    g.solveListValTurbineGeneratorReadPage = MagicMock(return_value=page)
    g.resubMax = 0  # NOTE: SHOULD BE in constructor
    g.turbchkfreq = 0
    g.status = dict(unfinished=len(jids), finished=0, success=0)
    g.res_re = [0] * 3  # NOTE: No idea what this is for..
    g.res = [None] * 3  # NOTE:??? HOLDER???  runListAsThread
    g.res_fin = [-1] * 3  # NOTE: runListAsThread

    g.solveListValTurbine(valueList=[jids], maxSend=20, sid=session_id, jobIds=jids)

    assert g.status["success"] == 3
    assert g.status["unfinished"] == 0
    assert len(g.res) == 3
    # WHY the items in g.res are set to dicts as a side effect of g.solveListValTurbine(),
    # but pylint can only infer their type based on their initial value of None in this function
    # related: the assignment of the g.res items in g,solveListValTurbine() requires them being None before
    # pylint: disable=unsubscriptable-object
    assert set([i["Id"] for i in g.res]) == set(jids)
    for i in g.res:
        assert i["session"] == session_id
        assert i["graphError"] == 0


@patch("foqus_lib.framework.graph.graph.Graph.solveListValTurbineGetGeneratorPage")
@patch("foqus_lib.framework.graph.graph.Graph.solveListValTurbineGeneratorReadPage")
def test_results_session_result_page_1_to_9(
    mock_read_generator_page, mock_get_generator_page
):
    """Paging results from session results generator

    graph.solveListValTurbine
    """
    _log = logging.getLogger(__name__)
    session_id = "6f85fc45-6044-478a-b56e-ac5f820eb861"
    result_id = "b6c71dc1-5c93-4526-99ef-07d6af0ba59f"

    # obj = results.Results()
    setName = "s3test"
    name = "whatever"
    # jids = map(lambda i: i['Id'], page)
    g = Graph()
    # g.solveListValTurbineCreateSession = MagicMock(return_value=session_id)
    g.solveListValTurbineGetGenerator = MagicMock(return_value=result_id)
    g.turbConfig.createSession = MagicMock(return_value=session_id)
    g.turbConfig.deleteCompletedJobsGen = MagicMock(return_value=None)

    # g.turbConfig.startSession = MagicMock(return_value=jids)

    test_results_session_result_page_1_to_9.page_num = 0

    def _get_page_num(arg):
        test_results_session_result_page_1_to_9.page_num += 1
        return test_results_session_result_page_1_to_9.page_num

    def _get_page(page_num):
        _log.debug("_get_page: %d" % page_num)
        fname = (
            "cloud/aws/test/data/s3/foqus-sessions/anonymous/%(session)s/%(result)s/%(page)d.json"
            % dict(session=session_id, result=result_id, page=page_num)
        )
        try:
            with open(fname) as fd:
                page = json.load(fd)
                ijids = [i["Id"] for i in page]
                g.turbConfig.createJobsInSession = MagicMock(return_value=ijids)
                return page
        except IOError:
            _log.error("IOError")
            return -2

    # mock_get_generator_page.return_value.get.side_effect = _get_page_num
    # mock_read_generator_page.return_value.get.side_effect= _get_page
    mock_get_generator_page.side_effect = list(range(1, 10))
    mock_read_generator_page.side_effect = [_get_page(i) for i in range(1, 10)]

    # NOTE: Getting the jids
    jids = list()
    test_results_session_result_page_1_to_9.page_num = 0
    page_num = 0
    for page in mock_read_generator_page.side_effect:
        _log.debug("JIDS: %s" % str(jids))
        jids += [i["Id"] for i in page]

    # RESET Page num
    test_results_session_result_page_1_to_9.page_num = 0
    mock_get_generator_page.side_effect = list(range(1, 10))
    mock_read_generator_page.side_effect = [_get_page(i) for i in range(1, 10)]

    g.resubMax = 0  # NOTE: SHOULD BE in constructor
    g.turbchkfreq = 0
    g.status = dict(unfinished=len(jids), finished=0, success=0, error=0)
    g.res_re = [0] * 18  # NOTE: No idea what this is for..
    g.res = [None] * 18  # NOTE:??? HOLDER???  runListAsThread
    g.res_fin = [-1] * 18  # NOTE: runListAsThread
    g.turbConfig.startSession = MagicMock(return_value=jids)
    assert 16 == len(jids)
    _log.debug("calling solveListValTurbine..")
    g.solveListValTurbine(valueList=[jids], maxSend=20, sid=session_id, jobIds=jids)

    _log.debug("Job Status: %s", g.status)
    assert g.status["success"] == 14
    assert g.status["unfinished"] == 0
    assert g.status["finished"] == 16
    assert g.status["error"] == 2

    # NOTE: Two jobs are None
    assert len(g.res) == 18
    assert g.res.count(None) == 2
    finished_jobs = [i for i in g.res if i is not None]

    # assert set(map(lambda i: i['Id'], g.res)) == set(jids)
    for i in finished_jobs:
        _log.debug("ID: %s", i["Id"])
        assert i["session"] == session_id
        assert i["graphError"] in [0, -3]
