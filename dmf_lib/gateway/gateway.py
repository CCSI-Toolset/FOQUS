import os
import platform
import subprocess
from dmf_lib.dialogs.status_dialog import StatusDialog
from dmf_lib.common.common import (
    DMF_HOME,
    JAVA_HOME,
    JAVA_JAR_PATH,
    GATEWAY_SCRIPTS_PATH,
    PRINT_COLON,
    WINDOWS
)

if platform.system().startswith(WINDOWS):
    try:
        import win32process
    except:
        pass


class Py4JGateway():
    def __init__(self, supressPopups=False):
        self.supressPopups = supressPopups

    def startupGateway(self):
        # Test if JAVA_HOME specified correctly
        java_home = os.environ[JAVA_HOME]
        if not os.path.exists(java_home):
            msg = "JAVA HOME path " + java_home + " is invalid"
            if not self.supressPopups:
                status = self.__class__.__name__ + '[StartupGateway]' + \
                    PRINT_COLON + msg
                StatusDialog.displayStatus(status)
            else:
                print msg
            return -1
        else:
            java_home_bin = os.path.join(java_home, 'bin')

        # Check if path to jar is present
        full_jar_path = os.environ[DMF_HOME] + JAVA_JAR_PATH
        if not os.path.exists(full_jar_path):
            if not self.supressPopups:
                StatusDialog.displayStatus(
                    "Please compile Java dependencies "
                    "before using DMF components.")
            return -3

        # Call java gateway script
        try:
            script_path = os.environ[DMF_HOME] + GATEWAY_SCRIPTS_PATH
            if platform.system().startswith(WINDOWS):  # We are on Windows
                java_exe_path = os.path.join(java_home_bin, 'javaw.exe')
                if not os.path.exists(java_exe_path):
                    msg = "javaw.exe not found in " + java_exe_path
                    if not self.supressPopups:
                        status = self.__class__.__name__ + '[StartupGateway]' + \
                            PRINT_COLON + msg
                        StatusDialog.displayStatus(status)
                    else:
                        print msg
                    return -2
                else:
                    new_env = os.environ.copy()
                    new_env[JAVA_HOME] = '"' + java_home + '"'
                    return subprocess.call(
                        [script_path + 'startup.bat', ''],
                        env=new_env,
                        creationflags=win32process.CREATE_NO_WINDOW)
            else:
                java_exe_path = os.path.join(java_home_bin, 'java')
                if not os.path.exists(java_exe_path):
                    msg = "java not found in " + java_exe_path
                    if not self.supressPopups:
                        status = self.__class__.__name__ + '[StartupGateway]' + \
                            PRINT_COLON + msg
                        StatusDialog.displayStatus(status)
                    else:
                        print msg
                    return -2
                else:
                    subprocess.call(
                        ['chmod', '0700', script_path + 'startup.sh'])
                    return subprocess.call([script_path + 'startup.sh', ''])
#                startup_script=subprocess.Popen([script_path + 'startup.sh'],
#                                   stdout = subprocess.PIPE,
#                                   stderr = subprocess.PIPE)
#                data = startup_script.stdout.readline() #block / wait
#                gateway_pid=data.rstrip('\n')
#                return gateway_pid
        except KeyError, e:
            if not self.supressPopups:
                status = self.__class__.__name__ + '[StartupGateway]' + \
                    PRINT_COLON + str(e)
                StatusDialog.displayStatus(status)
            raise KeyError('DMF_HOME not defined.')
        except Exception, e:
            if not self.supressPopups:
                status = self.__class__.__name__ + '[StartupGateway]' + \
                    PRINT_COLON + str(e)
                StatusDialog.displayStatus(status)
            raise

    def shutdownGateway(self):
        try:
            script_path = os.environ[DMF_HOME] + GATEWAY_SCRIPTS_PATH
            if platform.system().startswith(WINDOWS):  # We are on Windows
                # Check number of processes needing gateway
                p = subprocess.check_output(
                    [script_path + 'find_alive_dmf.bat'],
                    creationflags=win32process.CREATE_NO_WINDOW)
                n_running_dmf = int(p.rstrip('\n'))
                if n_running_dmf <= 1:
                    subprocess.Popen(
                        [script_path + 'shutdown.bat', ''],
                        env=os.environ.copy(),
                        stdout=subprocess.PIPE,
                        creationflags=win32process.CREATE_NO_WINDOW)
            else:
                subprocess.call(
                    ['chmod', '0700', script_path + 'find_alive_dmf.sh'])
                # Check number of processes needing gateway
                p = subprocess.check_output(
                    [script_path + 'find_alive_dmf.sh'])
                n_running_dmf = int(p.rstrip('\n'))
                if n_running_dmf <= 1:
                    subprocess.call(
                        ['chmod', '0700', script_path + 'shutdown.sh'])
                    res = subprocess.call([script_path + 'shutdown.sh', ''])
                    # Loop and kill all instances that are alive
                    while res == 0:
                        res = subprocess.call(
                            [script_path + 'shutdown.sh', ''])
                    return res
        except KeyError, e:
            if not self.supressPopups:
                status = self.__class__.__name__ + '[ShutdownGateway]' + \
                    PRINT_COLON + str(e)
                StatusDialog.displayStatus(status)
        except Exception, e:
            if not self.supressPopups:
                status = self.__class__.__name__ + '[ShutdownGateway]' + \
                    PRINT_COLON + str(e)
                StatusDialog.displayStatus(status)
