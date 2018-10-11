"""results_s3_test.py

* This contains tests for results instance

Joshua Boverhof, Lawrence Berekeley National Lab, 2018
John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
import json
from .. import results
from ... graph.graph import Graph
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

def test_results_empty():
    """ Paging results from session results generator
    solTime -- Amount of time used to solve graph outputs
    """
    sd = {
        'solTime':None,
        'input':dict(),
        'output':dict(),
        'graphError':None,
        'nodeError':{},
        'nodeSettings':{},
        'turbineMessages':{}
    }
    obj = results.Results()
    setName = 's3test'
    name = 'whatever'
    obj.addFromSavedValues(setName, name, valDict=sd)

    assert 5 == obj.count_cols()

def test_results_session_result_page_1():
    """ Paging results from session results generator

    graph.solveListValTurbine
    """
    session_id = '6f85fc45-6044-478a-b56e-ac5f820eb861'
    result_id = 'b6c71dc1-5c93-4526-99ef-07d6af0ba59f'
    fname = 'cloud/aws/test/data/s3/foqus-sessions/anonymous/%(session)s/%(result)s/%(page)s' %dict(
        session=session_id, result=result_id, page='1.json')

    with open(fname) as fd:
        page = json.load(fd)
        assert 3 == len(page)

    #obj = results.Results()
    setName = 's3test'
    name = 'whatever'
    jids = map(lambda i: i['Id'], page)
    g = Graph()
    #g.solveListValTurbineCreateSession = MagicMock(return_value=session_id)
    g.solveListValTurbineGetGenerator = MagicMock(return_value=result_id)
    g.turbConfig.createSession = MagicMock(return_value=session_id)
    g.turbConfig.deleteCompletedJobsGen = MagicMock(return_value=None)
    g.turbConfig.createJobsInSession = MagicMock(return_value=jids)
    g.turbConfig.startSession = MagicMock(return_value=jids)
    g.solveListValTurbineGetGeneratorPage = MagicMock(return_value=1)
    g.solveListValTurbineGeneratorReadPage = MagicMock(return_value=page)
    g.resubMax = 0 # NOTE: SHOULD BE in constructor
    g.turbchkfreq = 0
    g.status = dict(unfinished=len(jids), finished=0, success=0)
    g.res_re = [0]*3 # NOTE: No idea what this is for..
    g.res = [None]*3 # NOTE:??? HOLDER???  runListAsThread
    g.res_fin = [-1]*3 # NOTE: runListAsThread

    g.solveListValTurbine(valueList=[jids],
        maxSend=20,
        sid=session_id, jobIds=jids)

    assert g.status['success'] == 3
    assert g.status['unfinished'] == 0
    assert len(g.res) == 3
    assert set(map(lambda i: i['Id'], g.res)) == set(jids)
    for i in g.res:
        assert i['session'] == session_id
        assert i['graphError'] == 0

        
