"""foqus_service.py
* The AWS Cloud FOQUS service to start FOQUS

Joshua Boverhof, Lawrence Berkeley National Lab

See LICENSE.md for license and copyright details.
"""
import os,sys
import traceback
import win32api
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import os
import time
import sys,json,signal,os,errno,uuid,threading,traceback
from foqus_lib.service.flowsheet import FlowsheetControl
WORKING_DIRECTORY = os.path.join("\\ProgramData\\foqus_service")


"""
## GORILLA PATCH
Keep track of all messages created for a JOB ID, send unseen messages out to SNS
"""
from foqus_lib.framework.sim.turbineConfiguration import TurbineConfiguration
def getJobStatus(self, jobID, verbose=False, suppressLog=False):
    ret = TurbineConfiguration._getJobStatus(self, jobID, verbose=True, suppressLog=suppressLog)
    if getJobStatus._db is not None:
        if getJobStatus._jobid != jobID:
            getJobStatus._messages = []
            getJobStatus._jobid = jobID

        for msg in ret.get('Messages', []):
            if msg not in getJobStatus._messages:
                getJobStatus._messages.append(msg)
                getJobStatus._db.add_message(msg, jobid=jobID, flowsheet_jobid=getJobStatus._flowsheet_job_id)
    return ret

getJobStatus._db = None
getJobStatus._jobid = None
getJobStatus._flowsheet_job_id = None
getJobStatus._messages = []
TurbineConfiguration._getJobStatus = TurbineConfiguration.getJobStatus
TurbineConfiguration.getJobStatus = getJobStatus


class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "FOQUS-Cloud-Service"
    _svc_display_name_ = "FOQUS Cloud Service"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
        self._flowsheet_ctrl = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        servicemanager.LogInfoMsg("%s stop called" %(self._svc_name_))
        self._flowsheet_ctrl.stop()

    def SvcDoRun(self):
        """ Pop a job off FOQUS-JOB-QUEUE, call setup, then delete the job and call run.
        """
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self._flowsheet_ctrl = FlowsheetControl()
        self._flowsheet_ctrl.run()
        servicemanager.LogInfoMsg("%s exit run loop" %(self._svc_name_))


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)
