import json
import os
import subprocess
import shutil 
import time
from foqus_lib.framework.graph.nodeVars import *

def json2flowsheet(self, graph, filename=None):
        try:
            
            iREVEAL_work_dir = os.path.join(self.dat.foqusSettings.working_dir,'iREVEAL')
            iREVEAL_home = os.path.join(os.path.dirname(__file__), 'iREVEAL')
            iREVEAL_exe = os.path.join(iREVEAL_home,'iREVEAL.jar')
            print(iREVEAL_exe)
            input_file = os.path.join(iREVEAL_work_dir,os.path.basename(filename))
            shutil.copyfile(filename, input_file)
            paramIn_file = os.path.join(iREVEAL_work_dir, 'param.in')
            #delete graph.error variable
            graph.includeStatusOutput = False
            if 'error' in graph.output['graph']:
                del graph.output['graph']['error']
            #
            if "iREVEAL" not in graph.input.keys():
                graph.addNode("iREVEAL")
            else:
                del graph.input["iREVEAL"]
                del graph.output["iREVEAL"]
                graph.addNode("iREVEAL")
            
            print("java -jar " + iREVEAL_exe + " -s LHS -i " + input_file)
            process = subprocess.Popen([
                "java",
                "-jar",
                iREVEAL_exe,
                "-s",
                "LHS",
                "-i",
                input_file],
                cwd=iREVEAL_work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            line = process.stdout.readline()
            while process.poll() == None or line != '':
                if line == '': time.sleep(0.2)
                if line != '':
                    print(line.rstrip())
                line = process.stdout.readline()
                
            if os.path.exists(paramIn_file):
                in_input_section = None
                in_output_section = None
                with open(paramIn_file,'r') as f:
                    for line in f:
                        if len(line.strip()) == 0:
                            continue
                        if line.strip() == 'Input_Parameter_Starts':
                            in_input_section = True
                            continue
                        if line.strip() == 'Input_Parameter_Ends':
                            in_input_section = False
                            continue
                        if line.strip() == 'Output_Parameter_Starts':
                            in_output_section = True
                            continue
                        if line.strip() == 'Output_Parameter_Ends':
                            in_output_section = False
                            break
                        if in_input_section == True:
                            input_parameter = line.split()
                            print(input_parameter)
                            graph.input.addVariable(
                                    'iREVEAL', 
                                    input_parameter[0],
                                    nodeVars(
                                        value = 0.0, 
                                        vmin =  input_parameter[1],
                                        vmax = input_parameter[2], 
                                        vdflt = None,
                                        unit = "",
                                        vst = "user",
                                        vdesc = input_parameter[0],
                                        ts = 0,
                                        dtype = float))
                        if in_output_section == True:
                            output_parameter = line.split()
                            print(output_parameter)
                            graph.output.addVariable(
                                'iREVEAL',
                                output_parameter[0],
                                nodeVars(
                                    value=0.0,
                                    vmin=None,
                                    vmax=None,
                                    vdflt=None,
                                    unit="",
                                    vst="user",
                                    vdesc=output_parameter[0],
                                    ts=0,
                                    dtype=float))
            else:
                raise Exception('Cannot generate param.in !')
        
        
            print(graph.output['iREVEAL'].keys())
        
        except Exception as e:
            logging.getLogger("foqus." + __name__).\
            error("Problem running iREVEAL:\n" + traceback.format_exc())
