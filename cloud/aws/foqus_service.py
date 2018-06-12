import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import time
import logging
import logging.config
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.basicConfig(filename='TestService.log',level=logging.DEBUG)
_log = logging.getLogger()
_log.debug('Loading')

class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "FOQUS-Cloud-Service"
    _svc_display_name_ = "FOQUS Cloud Service"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        for i in range(1000):
            print "HI: %d" %i
            _log.info('Running: %d', i)
            time.sleep(1)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)
