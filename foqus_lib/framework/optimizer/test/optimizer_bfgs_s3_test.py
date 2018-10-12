"""results_s3_test.py

* This contains tests for results instance

Joshua Boverhof, Lawrence Berekeley National Lab, 2018
John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
import json
import logging
import time
from ... sampleResults import results
from ... graph.graph import Graph
from ..  import BFGS
from ..  import problem
try:
    from unittest.mock import MagicMock,patch
except ImportError:
    from mock import MagicMock,patch


@patch('foqus_lib.framework.graph.graph.Graph.solveListValTurbineGetGeneratorPage')
@patch('foqus_lib.framework.graph.graph.Graph.solveListValTurbineGeneratorReadPage')
def test_optimization_bfgs_session_results(mock_read_generator_page, mock_get_generator_page):
    """ Paging results from session results generator

    graph.solveListValTurbine
    """
    _log = logging.getLogger(__name__)
    assert BFGS.checkAvailable()
    opt = BFGS.opt()
    session_id = '6f85fc45-6044-478a-b56e-ac5f820eb861'
    result_id = 'b6c71dc1-5c93-4526-99ef-07d6af0ba59f'
    setName = 's3test'
    name = 'whatever'

    opt.graph = g = Graph()
    g.solveListValTurbineGetGenerator = MagicMock(return_value=result_id)
    g.turbConfig.createSession = MagicMock(return_value=session_id)
    g.turbConfig.deleteCompletedJobsGen = MagicMock(return_value=None)
    test_optimization_bfgs_session_results.page_num = 0
    def _get_page_num(arg):
        test_optimization_bfgs_session_results.page_num += 1
        return test_optimization_bfgs_session_results.page_num
    def _get_page(page_num):
        _log.debug("_get_page: %d" %page_num)
        fname = 'cloud/aws/test/data/s3/foqus-sessions/anonymous/%(session)s/%(result)s/%(page)d.json' %dict(
            session=session_id, result=result_id, page=page_num)
        try:
            with open(fname) as fd:
                page = json.load(fd)
                ijids = map(lambda i: i['Id'], page)
                g.turbConfig.createJobsInSession = MagicMock(return_value=ijids)
                return page
        except IOError:
            _log.error("IOError")
            return -2

    mock_get_generator_page.side_effect = range(1,10)
    mock_read_generator_page.side_effect = map(lambda i: _get_page(i), range(1,10))

    # NOTE: Getting the jids
    jids = list()
    test_optimization_bfgs_session_results.page_num = 0
    page_num = 0
    for page in mock_read_generator_page.side_effect:
        _log.debug("JIDS: %s" %str(jids))
        jids += map(lambda i: i['Id'], page)

    # RESET Page num
    test_optimization_bfgs_session_results.page_num = 0
    mock_get_generator_page.side_effect = range(1,10)
    mock_read_generator_page.side_effect = map(lambda i: _get_page(i), range(1,10))

    g.resubMax = 0 # NOTE: SHOULD BE in constructor
    g.turbchkfreq = 0
    g.status = dict(unfinished=len(jids), finished=0, success=0, error=0)
    g.res_re = [0]*18 # NOTE: No idea what this is for..
    g.res = [None]*18 # NOTE:??? HOLDER???  runListAsThread
    g.res_fin = [-1]*18 # NOTE: runListAsThread
    g.turbConfig.startSession = MagicMock(return_value=jids)
    assert 16 == len(jids)
    _log.debug("calling solveListValTurbine..")
    g.solveListValTurbine(valueList=[jids],
        maxSend=20,
        sid=session_id, jobIds=jids)

    _log.debug("Job Status: %s", g.status)
    assert g.status['success'] == 14
    assert g.status['unfinished'] == 0
    assert g.status['finished'] == 16
    assert g.status['error'] == 2

    # NOTE: Two jobs are None
    assert len(g.res) == 18
    assert g.res.count(None) == 2
    finished_jobs = filter(lambda i: i is not None, g.res)
    for i in finished_jobs:
        _log.debug("ID: %s", i['Id'])
        assert i['session'] == session_id
        assert i['graphError'] in [0,-3]

    # NOTE:  ERROR1 Must set opt.graph
    #   opt.graph = Graph()
    # >       xinit = self.graph.input.getFlat(self.prob.v, scaled=True)
    #E       AttributeError: 'NoneType' object has no attribute 'input'
    # NOTE:  ERROR2 Must set prob.v
    #   opt.prob = Problem()
    # >       xinit = self.graph.input.getFlat(self.prob.v, scaled=True)
    # E       AttributeError: 'NoneType' object has no attribute 'v'
    # NOTE:
    #>           setName = self.dat.flowsheet.results.incrimentSetName(setName)
    #E           AttributeError: 'NoneType' object has no attribute 'flowsheet'
    opt.prob = problem.problem()
    opt.options["Save results"].value = False
    # NOTE: scipy module
    #>       ores = scipy.optimize.minimize(
    #            self.f,
    #            xinit,
    #            method='L-BFGS-B',
    #            bounds=bounds,
    #            options={'ftol':ftol, 'eps':eps, 'maxfun':maxeval})
    #E       AttributeError: 'module' object has no attribute 'optimize'
    opt.optimize()
