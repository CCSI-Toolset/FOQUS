"""results_s3_test.py

* This contains tests for results instance

Joshua Boverhof, Lawrence Berekeley National Lab, 2018
John Eslick, Carnegie Mellon University, 2014
See LICENSE.md for license and copyright details.
"""
import json
from .. import results

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
    """
    fname = 'cloud/aws/test/data/s3/foqus-sessions/anonymous/6f85fc45-6044-478a-b56e-ac5f820eb861/b6c71dc1-5c93-4526-99ef-07d6af0ba59f/9.json'
    with open(fname) as fd:
        l = json.load(fd)
        assert 2 == len(l)

        
