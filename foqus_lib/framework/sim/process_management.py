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

"""process_management.py
* Process Management Utility for Terminating and Killing runnaway processes

Joshua Boverhof, Lawrence Berkeley National Lab

"""
import psutil
import logging

_log = logging.getLogger("foqus." + __name__)
_process_username = psutil.Process().username()


def _on_terminate(proc):
    _log.debug("process {} terminated with exit code {}".format(proc, proc.returncode))


def clean(names=["AspenProperties.exe", "am_task_server.exe", "sim_server.exe"]):
    """Scans Process Table for processes that should have exited,
    kills them if found.
    """
    p_list = [
        p
        for p in psutil.process_iter(attrs=["pid", "name", "username"])
        if p.info["username"] == _process_username and p.info["name"] in names
    ]
    _log.debug("Found Process: " + str(p_list))
    for process in p_list:
        _log.debug(
            "Terminate process PID=%s Name=%s Username=%s",
            process.info["pid"],
            process.info["name"],
            process.info["username"],
        )
        process.terminate()

    gone, alive = psutil.wait_procs(p_list, timeout=10, callback=_on_terminate)
    for p in alive:
        _log.debug(
            "Kill process PID=%s Name=%s Username=%s",
            process.info["pid"],
            process.info["name"],
            process.info["username"],
        )
        p.kill()
