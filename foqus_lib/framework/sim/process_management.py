
"""process_management.py
* Process Management Utility for Terminating and Killing runnaway processes

Joshua Boverhof, Lawrence Berkeley National Lab

See LICENSE.md for license and copyright details.
"""
import psutil
import logging
_log = logging.getLogger("foqus." + __name__)
_process_username = psutil.Process().username()

def _on_terminate(proc):
    _log.debug("process {} terminated with exit code {}".format(proc, proc.returncode))


def clean(names=['AspenProperties.exe', 'am_task_server.exe', 'sim_server.exe']):
    """ Scans Process Table for processes that should have exited,
    kills them if found.
    """
    p_list = [p for p in psutil.process_iter(attrs=['pid', 'name', 'username']) if p.info['username'] == _process_username and p.info['name'] in names]
    _log.debug("Found Process: " + str(p_list))
    for process in p_list:
        _log.debug("Terminate process PID=%s Name=%s Username=%s", process.info['pid'], process.info['name'], process.info['username'])
        process.terminate()

    gone, alive = psutil.wait_procs(p_list, timeout=10, callback=_on_terminate)
    for p in alive:
        _log.debug("Kill process PID=%s Name=%s Username=%s", process.info['pid'], process.info['name'], process.info['username'])
        p.kill()
