#
#FOQUS_SURROGATE_PLUGIN
#
# Surrogate plugins need to have FOQUS_SURROGATE_PLUGIN in the first
# 150 characters of text.  They also need to hav a .py extention and
# inherit the surrogate class.
#
#
# iREVEAL.py
#
# * This is an example of a surrogate model builder plugin for FOQUS, 
#   it uses the iREVEAL surrogate model builder program ref:
#
#
# * A setting of this plugin is the location of the iREVEAL executable 
#
#
# Poorva Sharma, Pacific Northwest National Lab, 2014
#
# This Material was produced under the DOE Carbon Capture Simulation
# Initiative (CCSI), and copyright is held by the software owners:
# ORISE, LANS, LLNS, LBL, PNNL, CMU, WVU, et al. The software owners
# and/or the U.S. Government retain ownership of all rights in the 
# CCSI software and the copyright and patents subsisting therein. Any
# distribution or dissemination is governed under the terms and 
# conditions of the CCSI Test and Evaluation License, CCSI Master
# Non-Disclosure Agreement, and the CCSI Intellectual Property 
# Management Plan. No rights are granted except as expressly recited
# in one of the aforementioned agreements.

import threading
import Queue
import logging
import subprocess
import os
import sys
import copy
import traceback
import time
import shutil
import csv
from foqus_lib.framework.surrogate.surrogate import surrogate
from foqus_lib.framework.uq.SurrogateParser import SurrogateParser
try:
    import win32process
except:
    pass

def checkAvailable():
    '''
        Plug-ins should have this function to check availability of any
        additional required software.  If requirements are not available
        plug-in will not be available.
    '''
    # I don't really check anything for now the ALAMO exec location is
    # just a setting of the plug-in, you may or may not need GAMS or 
    # MATLAB
    return True

class surrogateMethod(surrogate):
    metaDataJsonString = '''
    "CCSIFileMetaData":{
        "ID":"uuid",
        "CreationTime":"",
        "ModificationTime":"",
        "ChangeLog":[],
        "DisplayName":"",
        "OriginalFilename":"",
        "Application":"foqus_surogate_plugin",
        "Description":"iREVEAL FOQUS Plugin",
        "MIMEType":"application/ccsi+foqus",
        "Confidence":"testing",
        "Parents":[],
        "UpdateMetadata":True,
        "Version":""}
    '''
    
    def __init__(self, dat=None):
        '''
            iREVEAL interface constructor
        '''
        surrogate.__init__(self, dat)
        
        self.name = "iREVEAL"
        self.iREVEAL_dir = "iREVEAL"
        self.iREVEAL_home = os.path.join(os.path.dirname(__file__), 'iREVEAL')
        self.ex = None
        self.methodDescription = \
           ("<html>\n<head>"
             ".hangingindent {\n"
             "    margin-left: 22px ;\n"
             "    text-indent: -22px ;\n"
             "}\n"
             "</head>\n"
             "<b>iREVEAL: Reduced Order Model Builder </b>"
             "<p class=\"hangingindent\">"
             "Agarwal, K. Sharma, P. ; Jinliang Ma ; Chaomei Lo ; Gorton, I. ; Yan Liu <br>"
             "Reveal: An Extensible Reduced-Order Model Builder for Simulation and Modeling <br>"
             "Published in Computing in Science & Engineering  (Volume:16 ,  Issue: 2 ) <br>"
             "Mar.-Apr. 2014"
             "</p></html>")
        #self.options.add(
        #    name="Exe Path", 
        #    default= self.iREVEAL_home + os.sep + "iREVEAL.jar",
        #    dtype=str,
        #    desc="Path to the iREVEAL executable jar file")
        self.options.add(
            name="FOQUS Model (for UQ)", 
            default="ireveal_surrogate_uq.py",
            dtype=str,
            desc=".py file for UQ analysis")
        self.options.add(
            name="FOQUS Model (for Flowsheet)", 
            default="ireveal_surrogate_fs.py",
            dtype=str,
            desc=".py file flowsheet plugin, saved to user_plugins"\
                " in the working directory")
        self.options.add(
            name="Results File", 
            default="results",
            desc="Results File After Running Simulations")
        self.options.add(
            name="Regression Method", 
            default="Kriging",
            desc="Regression Method To Create Surrogate ROM",
            validValues=["Kriging"])
        self.createDir(self.iREVEAL_dir)
        
    def run(self):
        '''
            This function overloads the Thread class function,
            and is called when you run start() to start a new thread.
            
            a.    To create samples:
                    java -jar iREVEAL.jar -s LHS -i userInputFile.json
            
            b.    To run regressing analysis:
                    java -jar iREVEAL.jar -r resultsFile -d workingDir
            
            c.    To export model
                    java -jar iREVEAL.jar -e exportDir
            
        '''
        error = False
        #iREVEAL_exe = self.options["Exe Path"].value
        iREVEAL_exe = os.path.join(self.iREVEAL_home,'iREVEAL.jar')
        iREVEAL_work_dir = os.path.join(self.dat.foqusSettings.working_dir,self.iREVEAL_dir)
        results_file = os.path.join(iREVEAL_work_dir,self.options["Results File"].value)
        
        if os.path.exists(iREVEAL_exe) == False:
            self.msgQueue.put("Error: iREVEAL plugin location is not setup or is not correct. Please setup iREVEAL location in Foqus Settings.")
            self.result = {'outputEqns': 'Process terminated with error'}
            error = True
                
        # check if flowsheet is created
        if error == False:
            if hasattr(self.dat.foqusSettings, 'ireveal_input_file') == False:
                self.msgQueue.put("Error: No flowsheet created !! Please create a flowsheet by selecting iREVEAL input file.")
                self.result = {'outputEqns': 'Process terminated with error'}
                error = True
                
        # check if samples are created
        if error == False:
            #src_psuade_data_file = self.dat.foqusSettings.working_dir + os.sep + 'psuadeData'
            #src_psuade_in_file = self.dat.foqusSettings.working_dir + os.sep + 'psuade.in'
            dest_psuade_data_file = os.path.join(iREVEAL_work_dir,'psuadeData')
            dest_psuade_in_file = os.path.join(iREVEAL_work_dir,'psuade.in')
            #if os.path.exists(src_psuade_data_file) == False or os.path.exists(src_psuade_in_file) == False:
            if os.path.exists(dest_psuade_data_file) == False or os.path.exists(dest_psuade_in_file) == False:
                self.msgQueue.put("Error: Cannot find samples !! Please add samples first.")
                self.result = {'outputEqns': 'Process terminated with error'}
                error = True
                
        # check if results file is available
        if error == False:
            results_file = os.path.join(iREVEAL_work_dir ,'results')
            if os.path.exists(results_file) == False :
                self.msgQueue.put("Error: No results file in working directory.\n Please copy results file in "+iREVEAL_work_dir )
                self.result = {'outputEqns': 'Process terminated with error'}
                error = True
        
        if error == False : 
            
            #Copy required files
            src_input_file = self.dat.foqusSettings.ireveal_input_file
            dest_input_file = os.path.join(iREVEAL_work_dir,os.path.basename(src_input_file))
            shutil.copyfile(src_input_file, dest_input_file)
            
            #dest_psuade_data_file = iREVEAL_work_dir + os.sep + 'psuadeData'
            #shutil.copyfile(src_psuade_data_file, dest_psuade_data_file)
            
            #dest_psuade_in_file = iREVEAL_work_dir + os.sep + 'psuade.in'
            #shutil.copyfile(src_psuade_in_file, dest_psuade_in_file)
            
            self.msgQueue.put("------------------------------------")
            self.msgQueue.put("Starting iREVEAL Regression\n")
            self.msgQueue.put("Exe File Path:    " + iREVEAL_exe)
            self.msgQueue.put("Working-directory:     " + iREVEAL_work_dir)
            self.msgQueue.put("Results File Name:   " + results_file)
            self.msgQueue.put("------------------------------------")
            '''
            try:
                process = subprocess.Popen([
                    "java",
                    "-jar",
                    iREVEAL_exe,
                    "-s",
                    "LHS",
                    "-i",
                    dest_input_file],
                    cwd=iREVEAL_work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                line = process.stdout.readline()
                while process.poll() == None or line != '':
                    if line == '': time.sleep(0.2)
                    if line != '':
                        self.msgQueue.put(line.rstrip())
                    line = process.stdout.readline()
                    if self.stop.isSet():
                        self.msgQueue.put("**terminated by user**")
                        process.kill()
                        break
            except Exception as e:
                logging.getLogger("foqus." + __name__).\
                error("Problem running iREVEAL:\n" + traceback.format_exc())
                #should raise an exception here
            '''   
            try:
                process = subprocess.Popen([
                    "java",
                    "-jar",
                    iREVEAL_exe,
                    "-r",
                    results_file,
                    "-d",
                    iREVEAL_work_dir],
                    cwd=iREVEAL_work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin = None,
                    creationflags=win32process.CREATE_NO_WINDOW)
                line = process.stdout.readline()
                while process.poll() == None or line != '':
                    if line == '': time.sleep(0.2)
                    if line != '':
                        self.msgQueue.put(line.rstrip())
                    line = process.stdout.readline()
                    if self.stop.isSet():
                        self.msgQueue.put("**terminated by user**")
                        process.kill()
                        break
            #    self.msgQueue.put("Output Sampling File Name:  " + iREVEALSamplingFile)
            except Exception as e:
                logging.getLogger("foqus." + __name__).\
                error("Problem running iREVEAL:\n" + traceback.format_exc())
                #should raise an exception here
            
            '''
            predicted_results_file = iREVEAL_work_dir+os.sep+'Kriging'+os.sep+'predicted_results'
            with open(predicted_results_file, 'r') as f:
                reader = csv.reader(f, dialect='excel', delimiter='\t')
                output = ''
                for row in reader:
                    output = output + ' '.join(row) + '\n'
                
            self.result = {'outputEqns': output}
            '''
            
            try:
                print("java -jar" + iREVEAL_exe +" -e " + iREVEAL_work_dir)
                process = subprocess.Popen([
                    "java",
                    "-jar",
                    iREVEAL_exe,
                    "-e",
                    iREVEAL_work_dir],
                    cwd=iREVEAL_work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                line = process.stdout.readline()
                while process.poll() == None or line != '':
                    if line == '': time.sleep(0.2)
                    if line != '':
                        self.msgQueue.put(line.rstrip())
                    line = process.stdout.readline()
                    if self.stop.isSet():
                        self.msgQueue.put("**terminated by user**")
                        process.kill()
                        break
                #self.msgQueue.put("Output Sampling File Name:  CapeOpen.rom")
            except Exception as e:
                logging.getLogger("foqus." + __name__).\
                error("Problem running iREVEAL:\n" + traceback.format_exc())
                #should raise an exception here
            
            rom_file = os.path.join(iREVEAL_work_dir,'model.rom')
            with open(rom_file, 'r') as f:
                reader = csv.reader(f, dialect='excel', delimiter='\t')
                output = ''
                for row in reader:
                    output = output + ' '.join(row) + '\n'
            
            self.result = {'outputEqns': output}
            
            irData = SurrogateParser.parseIReveal(rom_file)
            
            output_var_ordered_dict = self.dat.flowsheet.output['iREVEAL']
            output_var_list = []
            for key in output_var_ordered_dict:
                output_var_list.append(key)
            ylabels = [output_var_list]             ### list of strings corresponding to output names
            print(irData, ylabels)
            irData = SurrogateParser.addIRevealOutputs(irData, ylabels)

            outfile = self.options["FOQUS Model (for UQ)"].value
            outfile2 = os.path.join(iREVEAL_work_dir, outfile)
            driverFile = SurrogateParser.writeIRevealDriver(irData, outfile2)
            driverFile2 = os.path.join(iREVEAL_work_dir, driverFile)
            self.msgQueue.put(
                "Wrote Python driver file: {0}".format(driverFile2))
            self.driverFile = driverFile2
            self.writePlugin()  # added by BN, 2/4/2016
        
    def writePlugin(self):  # added by BN, 2/4/2016
        file_name = self.options['FOQUS Model (for Flowsheet)'].value

        # Write the standard code top, then invoke UQ driver
        s = self.writePluginTop(method='iREVEAL', comments=['iREVEAL Flowsheet Model']) 
        with open(os.path.join('user_plugins', file_name), 'w') as f:
            f.write(s)
            lines = []
            lines.append('')
            lines.append('    def run(self):')
            lines.append('')
            lines.append('        # write input file')
            lines.append("        infileName = 'ireveal_fs.in'")
            lines.append("        f = open(infileName,'w')")
            lines.append('        nx = %d' % len(self.input))
            lines.append("        f.write('1 %d\\n' % nx)")
            lines.append("        f.write('1 ')")
            lines.append('        for val in self.inputvals:')
            lines.append("            f.write('%f ' % val)")
            lines.append("        f.write('\\n')")
            lines.append('        f.close()')
            lines.append('')
            lines.append('        # for each output, invoke UQ driver based on that output''s trained model')
            lines.append('        for i, vname in enumerate(self.outputs):')
            lines.append("            outfileName = 'ireveal_fs.out%d' % i")
            lines.append("            p = subprocess.Popen(['python', r'%s', infileName, outfileName, '{0}'.format(i)]," % self.driverFile)
            lines.append('                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)')
            lines.append('            stdout, stderr = p.communicate()')
            lines.append('            if stdout:')
            lines.append('                print stdout')
            lines.append('            if stderr:') 
            lines.append('                print stderr')
            lines.append('')
            lines.append('            # read results and instantiate output value')
            lines.append("            ypred = numpy.loadtxt(outfileName)")
            lines.append('            self.outputs[vname].value = ypred[1]')
            lines.append('')
            f.write('\n'.join(lines))

        self.dat.reloadPlugins()

            
