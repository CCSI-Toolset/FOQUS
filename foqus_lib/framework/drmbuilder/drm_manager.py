# drm_manager.py
import os.path
import json
import math
import numpy as np
from subprocess import Popen, PIPE
from itertools import chain
from input_variable import InputVariable
from output_variable import OutputVariable
from step_change import StepChange
from dabnet_input import DABNetInput
from narma_input import NARMAInput
from uq_input import UQInput
from drm_container import DRMContainer
from plotting_input import PlottingInput
from acm_input import ACMInput
from PySide.QtGui import *
import DLLs.pyDRMSampling as DRMSampling
import DLLs.pyDRMTraining as DRMTraining


class DRMManager(object):
    """
        The document class for a D-RM Builder case
    """
    def __init__(self):
        self.simsinter_exe = None                   # executable to run ACM, assigned by MainDRMBuilder window, not saved
        self.doc_name = 'case1'                     # document or case name, not saved to dictionary or case file
        self.simsinter_config = 'case1.json'        # SimSinter configureation file name
        self.bsaved = False                         # true if the instance has been saved
        self.bmodified = False                      # true if the case is modified
        self.bhfm_file = False                      # true if high-fidelity model file has been specified
        self.binputready = False                    # true if input variable list has been assembled
        self.boutputready = False                   # true if output variable list has been assembled
        self.bsequence_train = False                # true if training sequence has been generated
        self.bsequence_valid = False                # true if validation sequence has been generated
        self.brun_train = False                     # true if high-fidelity simulation for training has been completed
        self.brun_valid = False                     # true if high-fidelity simulation for validation has been completed
        self.bbuilt_dabnet = False                  # true if DABNet DRM model has been generated
        self.bbuilt_narma = False                   # true if NARMA DRM model has been generated
        self.bpredict_train = False                 # true if training response is predicted by DRM
        self.bpredict_valid = False                 # true if validation response is predicted by DRM
        self.bnoise_set = False                     # true if noise related to Q and R is set
        self.brun_uq = False                        # true if UQ calculation is performed
        self.bthread = False                        # true if thread is running, no save to case file
        self.msg = ""                               # message string for the message area
        self.imodel_type = 0                        # model type 0=DABNET, 1=NARMA
        self.ipredict_opt_dabnet = 1                # model DABNET prediction option 0=Laguerre, 1=balanced
        self.ipredict_opt_narma = 0                 # model NARMA prediction option 0=use high-fidelity model history, 1=use accumulated NARMA predicted history
        self.input_list_all = list()                # all input variable list
        self.input_list_sel = list()                # selected input variable list
        self.output_list_all = list()               # all output variable list
        self.output_list_sel = list()               # selected output variable list
        self.step_change_train = StepChange()       # step change for training
        self.step_change_valid = StepChange()       # step change for validation
        self.acm_input = ACMInput()                 # high-fidelity model (ACM) input data
        self.dabnet_input = DABNetInput()           # DABNet model user inputs
        self.narma_input = NARMAInput()             # NARMA model user inputs
        self.plotting_input = PlottingInput()       # user inputs for plotting results including UQ, not saved in case file
        self.uq_input = UQInput()                   # UQ input related to process and output noise
        self.sequence_train = None                  # step change sequence for training
        self.sequence_valid = None                  # step change sequence for validation
        self.nramp_steps_train = list()             # additional ramp steps added for each sampling step of training
        self.nramp_steps_valid = list()             # additional ramp steps added for each sampling step of validation
        self.acm_result_ramp_train = None           # ACM results with ramp for training
        self.acm_result_ramp_valid = None           # ACM results with ramp for validation
        self.acm_result_train = None                # ACM results for training with ramp points filtered out
        self.acm_result_valid = None                # ACM results for validation with ramp points filtered out
        self.drm_prediction_train = None            # DRM prediction for training sequence (varied output only)
        self.drm_prediction_valid = None            # DRM prediction for validation sequence (varied output only)
        self.ukf_prediction_valid = None            # UKF prediction for validation sequence (varied output only)
        self.ukf_observation_valid = None           # UKF observed response for validation (varied output only)
        self.ukf_std_valid = None                   # UKF standard deviation of response for validation (varied output only)
        self.rsquared_train = 1                     # R^2 between DRM and ACM for training
        self.rsquared_valid = 1                     # R^2 between DRM and ACM for validation
        self.rsquared_valid_ukf = 1                 # R^2 between UKF and ACM for validation
        self.cov_state = None                       # covariance of state variables from UKF filter
        self.cov_output = None                      # covariance of output variables from UKF filter
        self.drm_container = None

    def to_dictionary(self):
        dict_data = dict()
        dict_data['simsinter_config'] = self.simsinter_config
        dict_data['bmodified'] = self.bmodified
        dict_data['bhfm_file'] = self.bhfm_file
        dict_data['binputready'] = self.binputready
        dict_data['boutputready'] = self.boutputready
        dict_data['bsequence_train'] = self.bsequence_train
        dict_data['bsequence_valid'] = self.bsequence_valid
        dict_data['brun_train'] = self.brun_train
        dict_data['brun_valid'] = self.brun_valid
        dict_data['bbuilt_dabnet'] = self.bbuilt_dabnet
        dict_data['bbuilt_narma'] = self.bbuilt_narma
        dict_data['bpredict_train'] = self.bpredict_train
        dict_data['bpredict_valid'] = self.bpredict_valid
        dict_data['bnoise_set'] = self.bnoise_set
        dict_data['brun_uq'] = self.brun_uq
        dict_data['bthread'] = self.bthread
        dict_data['msg'] = self.msg
        dict_data['imodel_type'] = self.imodel_type
        dict_data['ipredict_opt_dabnet'] = self.ipredict_opt_dabnet
        dict_data['ipredict_opt_narma'] = self.ipredict_opt_narma
        dict_data['input_list_all'] = self.to_list(self.input_list_all)
        dict_data['input_list_sel'] = self.to_list(self.input_list_sel)
        dict_data['output_list_all'] = self.to_list(self.output_list_all)
        dict_data['output_list_sel'] = self.to_list(self.output_list_sel)
        dict_data['step_change_train'] = self.step_change_train.to_dictionary()
        dict_data['step_change_valid'] = self.step_change_valid.to_dictionary()
        dict_data['acm_input'] = self.acm_input.to_dictionary()
        dict_data['dabnet_input'] = self.dabnet_input.to_dictionary()
        dict_data['narma_input'] = self.narma_input.to_dictionary()
        dict_data['plotting_input'] = self.plotting_input.to_dictionary()
        dict_data['uq_input'] = self.uq_input.to_dictionary()
        if self.bsequence_train:
            dict_data['sequence_train'] = self.sequence_train
        if self.bsequence_valid:
            dict_data['sequence_valid'] = self.sequence_valid
        if self.brun_train:
            dict_data['acm_result_train'] = self.acm_result_train
            dict_data['acm_result_ramp_train'] = self.acm_result_ramp_train
            dict_data['nramp_steps_train'] = self.nramp_steps_train
        if self.brun_valid:
            dict_data['acm_result_valid'] = self.acm_result_valid
            dict_data['acm_result_ramp_valid'] = self.acm_result_ramp_valid
            dict_data['nramp_steps_valid'] = self.nramp_steps_valid
        if self.bpredict_train:
            dict_data['drm_prediction_train'] = self.drm_prediction_train
            dict_data['rsquared_train'] = self.rsquared_train
        if self.bpredict_valid:
            dict_data['drm_prediction_valid'] = self.drm_prediction_valid
            dict_data['rsquared_valid'] = self.rsquared_valid
        if self.bbuilt_dabnet or self.bbuilt_narma:
            dict_data['drm_container'] = self.drm_container.to_dictionary()
        if self.brun_uq:
            dict_data['ukf_observation_valid'] = self.ukf_observation_valid
            dict_data['ukf_prediction_valid'] = self.ukf_prediction_valid
            dict_data['rsquared_valid_ukf'] = self.rsquared_valid_ukf
            dict_data['cov_state'] = self.cov_state.tolist()
            dict_data['cov_output'] = self.cov_output.tolist()
        return dict_data

    def to_list(self, var_list):
        list_data = []
        for item in var_list:
            list_data.append(item.to_dictionary())
        return list_data

    def from_dictionary(self, dict_data):
        self.simsinter_config = dict_data['simsinter_config']
        self.bmodified = dict_data['bmodified']
        self.bhfm_file = dict_data['bhfm_file']
        self.binputready = dict_data['binputready']
        self.boutputready = dict_data['boutputready']
        self.bsequence_train = dict_data['bsequence_train']
        self.bsequence_valid = dict_data['bsequence_valid']
        self.brun_train = dict_data['brun_train']
        self.brun_valid = dict_data['brun_valid']
        self.bbuilt_dabnet = dict_data['bbuilt_dabnet']
        self.bbuilt_narma = dict_data['bbuilt_narma']
        self.bpredict_train = dict_data['bpredict_train']
        self.bpredict_valid = dict_data['bpredict_valid']
        self.bnoise_set = dict_data['bnoise_set']
        self.brun_uq = dict_data['brun_uq']
        self.bthread = dict_data['bthread']
        self.msg = dict_data['msg']
        self.imodel_type = dict_data['imodel_type']
        self.ipredict_opt_dabnet = dict_data['ipredict_opt_dabnet']
        self.ipredict_opt_narma = dict_data['ipredict_opt_narma']
        self.input_list_all = self.from_input_list(dict_data['input_list_all'])
        self.input_list_sel = self.from_input_list(dict_data['input_list_sel'])
        self.output_list_all = self.from_output_list(dict_data['output_list_all'])
        self.output_list_sel = self.from_output_list(dict_data['output_list_sel'])
        self.step_change_train.from_dictionary(dict_data['step_change_train'])
        self.step_change_valid.from_dictionary(dict_data['step_change_valid'])
        self.acm_input.from_dictionary(dict_data['acm_input'])
        self.dabnet_input.from_dictionary(dict_data['dabnet_input'])
        self.narma_input.from_dictionary(dict_data['narma_input'])
        self.plotting_input.from_dictionary(dict_data['plotting_input'])
        self.uq_input.from_dictionary(dict_data['uq_input'])
        if self.bsequence_train:
            self.sequence_train = dict_data['sequence_train']
        if self.bsequence_valid:
            self.sequence_valid = dict_data['sequence_valid']
        if self.brun_train:
            self.acm_result_train = dict_data['acm_result_train']
            self.acm_result_ramp_train = dict_data['acm_result_ramp_train']
            self.nramp_steps_train = dict_data['nramp_steps_train']
        if self.brun_valid:
            self.acm_result_valid = dict_data['acm_result_valid']
            self.acm_result_ramp_valid = dict_data['acm_result_ramp_valid']
            self.nramp_steps_valid = dict_data['nramp_steps_valid']
        if self.bpredict_train:
            self.drm_prediction_train = dict_data['drm_prediction_train']
            self.rsquared_train = dict_data['rsquared_train']
        if self.bpredict_valid:
            self.drm_prediction_valid = dict_data['drm_prediction_valid']
            self.rsquared_valid = dict_data['rsquared_valid']
        if self.bbuilt_dabnet or self.bbuilt_narma:
            self.drm_container = DRMContainer()
            self.drm_container.from_dictionary(dict_data['drm_container'])
        if self.brun_uq:
            self.ukf_observation_valid = dict_data['ukf_observation_valid']
            self.ukf_prediction_valid = dict_data['ukf_prediction_valid']
            self.rsquared_valid_ukf = dict_data['rsquared_valid_ukf']
            cov_state_list = dict_data['cov_state']
            cov_output_list = dict_data['cov_output']
            self.cov_state = np.matrix(cov_state_list)
            self.cov_output = np.matrix(cov_output_list)

    def from_input_list(self, var_list):
        list_data = []
        for item in var_list:
            input_variable = InputVariable()
            input_variable.from_dictionary(item)
            list_data.append(input_variable)
        return list_data

    def from_output_list(self, var_list):
        list_data = []
        for item in var_list:
            output_variable = OutputVariable()
            output_variable.from_dictionary(item)
            list_data.append(output_variable)
        return list_data

    def write_to_json_file(self, file_name):
        dict_data = self.to_dictionary()
        with open(file_name, 'w') as fout:
            json.dump(dict_data, fout, indent=2)
        self.bsaved = True
        self.bmodified = False

    def read_from_json_file(self, file_name):
        with open(file_name, 'r') as fin:
            dict_data = json.load(fin)
        self.from_dictionary(dict_data)
        self.bsaved = True
        self.bmodified = False

    def write_to_matlab_file(self, file_name):
        with open(file_name, 'w') as fout:
            if self.imodel_type == 0:
                fout.write("DRM_type = \'DABNet\';\n")
            else:
                fout.write("DRM_type = \'NARMA\';\n")
            line = "dt = {0};\n".format(self.acm_input.dt_sampling)
            fout.write(line)
            line = "dt_unit = \'{}\';\n".format(self.acm_input.unit_time)
            fout.write(line)
            ninput_all = len(self.input_list_all)
            noutput_all = len(self.output_list_all)
            line = "ninput = {};\n".format(ninput_all)
            fout.write(line)
            line = "noutput = {};\n".format(noutput_all)
            fout.write(line)
            input_names = "input_names = {"
            input_descs = "input_descs = {"
            input_units = "input_units = {"
            input_indices = "input_indices = ["
            input_lowers = "input_lowers = {"
            input_uppers = "input_uppers = {"
            for i in xrange(ninput_all):
                input_names += "\'" + self.input_list_all[i].key_sinter + "\' "
                input_descs += "\'" + self.input_list_all[i].desc + "\' "
                input_units += "\'" + self.input_list_all[i].unit + "\' "
                if self.input_list_all[i].bvaried:
                    input_indices += "{} ".format(i+1)
                    input_lowers += "{} ".format(self.input_list_all[i].xlower)
                    input_uppers += "{} ".format(self.input_list_all[i].xupper)
                else:
                    input_lowers += "{} ".format(self.input_list_all[i].xdefault)
                    input_uppers += "{} ".format(self.input_list_all[i].xdefault)
            fout.write(input_names.rstrip() + "};\n")
            fout.write(input_descs.rstrip() + "};\n")
            fout.write(input_units.rstrip() + "};\n")
            fout.write(input_indices.rstrip() + "];\n")
            fout.write(input_lowers.rstrip() + "};\n")
            fout.write(input_uppers.rstrip() + "};\n")
            output_names = "output_names = {"
            output_descs = "output_descs = {"
            output_units = "output_units = {"
            output_indices = "output_indices = ["
            for i in xrange(noutput_all):
                output_names += "\'" + self.output_list_all[i].key_sinter + "\' "
                output_descs += "\'" + self.output_list_all[i].desc + "\' "
                output_units += "\'" + self.output_list_all[i].unit + "\' "
                if self.output_list_all[i].bvaried:
                    output_indices += "{} ".format(i+1)
            fout.write(output_names.rstrip() + "};\n")
            fout.write(output_descs.rstrip() + "};\n")
            fout.write(output_units.rstrip() + "};\n")
            fout.write(output_indices.rstrip() + "];\n")
            self.drm_container.write_to_matlab_file(self.imodel_type, fout)

    def write_to_training_data_file(self, file_name):
        # calculate the time series
        dt = self.acm_input.dt_sampling
        unit_time = self.acm_input.unit_time
        ninput_all = len(self.input_list_all)
        noutput_all = len(self.output_list_all)
        noutput_sel = len(self.output_list_sel)
        npair = len(self.acm_result_train[0])
        with open(file_name, 'w') as fout:
            fout.write("Time ({})".format(unit_time))
            for i in xrange(ninput_all):
                fout.write(",{} ({})".format(self.input_list_all[i].key_sinter, self.input_list_all[i].unit))
            for i in xrange(noutput_all):
                fout.write(",{} ({})".format(self.output_list_all[i].key_sinter, self.output_list_all[i].unit))
            if (self.bpredict_train):
                for i in xrange(noutput_all):
                    if self.output_list_all[i].bvaried:
                        fout.write(",{}_DRM ({})".format(self.output_list_all[i].key_sinter, self.output_list_all[i].unit))
            fout.write("\n")
            for j in xrange(npair):
                fout.write("{}".format(dt*j))
                for i in xrange(ninput_all):
                    fout.write(",{}".format(self.acm_result_train[i][j]))
                for i in xrange(noutput_all):
                    fout.write(",{}".format(self.acm_result_train[i+ninput_all][j]))
                if (self.bpredict_train):
                    for i in xrange(noutput_sel):
                        fout.write(",{}".format(self.drm_prediction_train[i][j]))
                fout.write("\n")

    def write_to_validation_data_file(self, file_name):
        dt = self.acm_input.dt_sampling
        unit_time = self.acm_input.unit_time
        ninput_all = len(self.input_list_all)
        noutput_all = len(self.output_list_all)
        noutput_sel = len(self.output_list_sel)
        npair = len(self.acm_result_valid[0])
        with open(file_name, 'w') as fout:
            fout.write("Time ({})".format(unit_time))
            for i in xrange(ninput_all):
                fout.write(",{} ({})".format(self.input_list_all[i].key_sinter, self.input_list_all[i].unit))
            for i in xrange(noutput_all):
                fout.write(",{} ({})".format(self.output_list_all[i].key_sinter, self.output_list_all[i].unit))
            if (self.bpredict_valid):
                for i in xrange(noutput_all):
                    if self.output_list_all[i].bvaried:
                        fout.write(",{}_DRM ({})".format(self.output_list_all[i].key_sinter, self.output_list_all[i].unit))
            fout.write("\n")
            for j in xrange(npair):
                fout.write("{}".format(dt*j))
                for i in xrange(ninput_all):
                    fout.write(",{}".format(self.acm_result_valid[i][j]))
                for i in xrange(noutput_all):
                    fout.write(",{}".format(self.acm_result_valid[i+ninput_all][j]))
                if (self.bpredict_valid):
                    for i in xrange(noutput_sel):
                        fout.write(",{}".format(self.drm_prediction_valid[i][j]))
                fout.write("\n")

    def write_to_covariance_matrices_file(self, file_name):
        nstate = self.cov_state.shape[0]
        nout = self.cov_output.shape[0]
        q_arr = np.zeros((nstate, nstate))
        r_arr = np.zeros((nout, nout))
        for i in xrange(nstate):
            std = self.uq_input.fq_state*self.drm_container.sigma_state[i]
            q_arr[i][i] = std*std
        for i in xrange(nout):
            std = self.uq_input.fr_output[i]*self.drm_container.sigma_out[i]
            r_arr[i][i] = std*std
        with open(file_name, 'w') as fout:
            fout.write("Noise matrix of state space variables: {}x{}\n".format(nstate, nstate))
            for i in xrange(nstate):
                for j in xrange(nstate-1):
                    fout.write("{}, ".format(q_arr[i][j]))
                fout.write("{}\n".format(q_arr[i][nstate-1]))
            fout.write("Noise matrix of measured output variables: {}x{}\n".format(nout, nout))
            for i in xrange(nout):
                for j in xrange(nout-1):
                    fout.write("{}, ".format(r_arr[i][j]))
                fout.write("{}\n".format(r_arr[i][nout-1]))
            fout.write("Covariance matrix of state space variables: {}x{}\n".format(nstate, nstate))
            for i in xrange(nstate):
                for j in xrange(nstate-1):
                    fout.write("{}, ".format(self.cov_state[i, j]))
                fout.write("{}\n".format(self.cov_state[i, nstate-1]))
            fout.write("Covariance matrix of output variables: {}x{}\n".format(nout, nout))
            for i in xrange(nout):
                for j in xrange(nout-1):
                    fout.write("{}, ".format(self.cov_output[i, j]))
                fout.write("{}\n".format(self.cov_output[i, nout-1]))

    def write_to_log_file(self, file_name):
        with open(file_name, 'w') as fout:
            fout.write(self.msg)

    def update_selected_input_list(self):
        self.input_list_sel = []
        for item in self.input_list_all:
            if item.bvaried:
                self.input_list_sel.append(item)

    def update_selected_output_list(self):
        self.output_list_sel = []
        for item in self.output_list_all:
            if item.bvaried:
                self.output_list_sel.append(item)

    def get_selected_output_index_from_index_of_all(self, iall):
        if iall < 0 or iall >= len(self.output_list_all):
            return -1
        if self.output_list_all[iall].bvaried == False:
            return -1
        isel = -1
        for i in xrange(iall+1):
            if self.output_list_all[i].bvaried:
                isel += 1
        return isel

    def parse_simsinter_config(self):
        with open(self.simsinter_config, 'r') as fin:
            dict_data = json.load(fin)
        if not dict_data['settings']['RunMode']['default']=='Dynamic':
            QMessageBox.warning(None, 'Warning', 'Run mode is not configured to the dynamic mode')
            return False
        if not os.path.isfile(dict_data['aspenfile']):
            QMessageBox.warning(None, 'Warning', 'ACM file {} specified in SimSinter configuration file is not found'.format(dict_data['aspenfile']))
            return False
        self.acm_input.unit_time = dict_data['settings']['TimeUnits']['default']
        self.acm_input.dt_min_solver = dict_data['settings']['MinStepSize']['default']
        del self.input_list_all[:]
        del self.output_list_all[:]
        for k, v in dict_data['dynamic-inputs'].items():
            if v['type']=='double':
                input_var = InputVariable()
                input_var.key_sinter = k
                input_var.name = v['path'][0]
                input_var.desc = v['description']
                input_var.unit = v['units']
                input_var.xdefault = v['default']
                if v.has_key('min'):
                    input_var.xlower = v['min']
                else:
                    input_var.xlower = input_var.xdefault*0.9
                if v.has_key('max'):
                    input_var.xupper = v['max']
                else:
                    input_var.xupper = input_var.xdefault*1.1
                self.input_list_all.append(input_var)
        self.update_selected_input_list()
        for k, v in dict_data['dynamic-outputs'].items():
            if v['type']=='double':
                output_var = OutputVariable()
                output_var.key_sinter = k
                output_var.name = v['path'][0]
                output_var.desc = v['description']
                output_var.unit = v['units']
                output_var.xdefault = v['default']
                self.output_list_all.append(output_var)
        self.update_selected_output_list()
        return True

    def sample_for_training(self):
        rand_seed = 0.0
        ndim = len(self.input_list_sel)
        duration0 = 5
        vbvaried = []
        vxdefault = []
        vxlower = []
        vxupper = []
        for item in self.input_list_all:
            vbvaried.append(item.bvaried)
            vxdefault.append(item.xdefault)
            vxlower.append(item.xlower)
            vxupper.append(item.xupper)
        # DRMSampling.sample_input_space() return a step change sequence including constant input variables
        self.sequence_train = DRMSampling.sample_input_space(rand_seed, ndim, self.step_change_train.ireverse, self.step_change_train.npoint, self.step_change_train.nduration, duration0, self.step_change_train.vduration, vbvaried, vxdefault, vxlower, vxupper)

    def sample_for_validation(self):
        rand_seed = 1.0
        ndim = len(self.input_list_sel)
        duration0 = 5
        vbvaried = []
        vxdefault = []
        vxlower = []
        vxupper = []
        for item in self.input_list_all:
            vbvaried.append(item.bvaried)
            vxdefault.append(item.xdefault)
            vxlower.append(item.xlower)
            vxupper.append(item.xupper)
        # DRMSampling.sample_input_space() return a step change sequence including constant input variables
        self.sequence_valid = DRMSampling.sample_input_space(rand_seed, ndim, self.step_change_valid.ireverse, self.step_change_valid.npoint, self.step_change_valid.nduration, duration0, self.step_change_valid.vduration, vbvaried, vxdefault, vxlower, vxupper)

    def prepare_input_json_for_training(self):
        dict_data = dict()
        dict_data['RunMode'] = "Dynamic"
        dict_data['printlevel'] = 0
        dict_data['homotopy'] = 0
        ninput_all = len(self.input_list_all)
        nstep = len(self.sequence_train)/ninput_all
        dt = self.acm_input.dt_sampling
        dt_ramp = self.acm_input.dt_ramp
        step_list = [None]*ninput_all
        step_list_ramp = [None]*ninput_all
        time_series = []
        for j in xrange(ninput_all):
            step_list[j] = [None]*nstep
            step_list_ramp[j] = []
        for i in xrange(nstep):
            for j in xrange(ninput_all):
                step_list[j][i] = self.sequence_train[i*ninput_all+j]
        # now add ramp points if necessary
        bramp = [None]*ninput_all
        for j in xrange(ninput_all):    # use ramp only if the input variable is varied and ramped
            bramp[j] = self.input_list_all[j].bvaried and self.input_list_all[j].bramp
        self.nramp_steps_train = [None]*nstep
        # first point is the steady state point and without step change
        t = dt
        time_series.append(t)
        self.nramp_steps_train[0] = 0
        for j in xrange(ninput_all):
            step_list_ramp[j].append(step_list[j][0])
        for i in xrange(1, nstep):  # loop through remaining steps
            nextra = 0
            for j in xrange(ninput_all):    # there is no step change of multiple variables
                if bramp[j] and step_list[j][i] != step_list[j][i-1]:   # step change found
                    npoint_f = math.ceil(abs(step_list[j][i] - step_list[j][i-1])/self.input_list_all[j].ramp_rate/dt_ramp)
                    nextra = int(npoint_f) - 1
                    jramp = j
                    break
            self.nramp_steps_train[i] = nextra
            for k in xrange(nextra):
                t += dt_ramp
                time_series.append(t)
                for j in xrange(ninput_all):
                    if j == jramp:
                        uk = step_list[j][i-1] + math.copysign((k+1)*dt_ramp*self.input_list_all[j].ramp_rate, step_list[j][i]-step_list[j][i-1])
                        step_list_ramp[j].append(uk)
                    else:
                        step_list_ramp[j].append(step_list[j][i])
            t = (i+1)*dt
            time_series.append(t)
            for j in xrange(ninput_all):
                step_list_ramp[j].append(step_list[j][i])
        dict_data['TimeSeries'] = time_series
        j = 0
        for item in self.input_list_all:
            dict_data[item.key_sinter] = step_list_ramp[j]
            j += 1
        file_name = self.doc_name + "_train_input.json"
        with open(file_name, 'w') as fout:
            json.dump(dict_data, fout, indent=2)

    def prepare_input_json_for_validation(self):
        dict_data = dict()
        dict_data['RunMode'] = "Dynamic"
        dict_data['printlevel'] = 0
        dict_data['homotopy'] = 0
        ninput_all = len(self.input_list_all)
        nstep = len(self.sequence_valid)/ninput_all
        dt = self.acm_input.dt_sampling
        dt_ramp = self.acm_input.dt_ramp
        step_list = [None]*ninput_all
        step_list_ramp = [None]*ninput_all
        time_series = []
        for j in xrange(ninput_all):
            step_list[j] = [None]*nstep
            step_list_ramp[j] = []
        for i in xrange(nstep):
            for j in xrange(ninput_all):
                step_list[j][i] = self.sequence_valid[i*ninput_all+j]
        # now add ramp points if necessary
        bramp = [None]*ninput_all
        for j in xrange(ninput_all):    # use ramp only if the input variable is varied and ramped
            bramp[j] = self.input_list_all[j].bvaried and self.input_list_all[j].bramp
        self.nramp_steps_valid = [None]*nstep
        # first point is the steady state point and without step change
        t = dt
        time_series.append(t)
        self.nramp_steps_valid[0] = 0
        for j in xrange(ninput_all):
            step_list_ramp[j].append(step_list[j][0])
        for i in xrange(1, nstep):  # loop through remaining steps
            nextra = 0
            for j in xrange(ninput_all):    # there is no step change of multiple variables
                if bramp[j] and step_list[j][i] != step_list[j][i-1]:   # step change found
                    npoint_f = math.ceil(abs(step_list[j][i] - step_list[j][i-1])/self.input_list_all[j].ramp_rate/dt_ramp)
                    nextra = int(npoint_f) - 1
                    jramp = j
                    break
            self.nramp_steps_valid[i] = nextra
            for k in xrange(nextra):
                t += dt_ramp
                time_series.append(t)
                for j in xrange(ninput_all):
                    if j == jramp:
                        uk = step_list[j][i-1] + math.copysign((k+1)*dt_ramp*self.input_list_all[j].ramp_rate, step_list[j][i]-step_list[j][i-1])
                        step_list_ramp[j].append(uk)
                    else:
                        step_list_ramp[j].append(step_list[j][i])
            t = (i+1)*dt
            time_series.append(t)
            for j in xrange(ninput_all):
                step_list_ramp[j].append(step_list[j][i])
        dict_data['TimeSeries'] = time_series
        j = 0
        for item in self.input_list_all:
            dict_data[item.key_sinter] = step_list_ramp[j]
            j += 1
        file_name = self.doc_name + "_valid_input.json"
        with open(file_name, 'w') as fout:
            json.dump(dict_data, fout, indent=2)

    def run_acm_training(self):
        self.prepare_input_json_for_training()
        train_input = self.doc_name + "_train_input.json"
        train_output = self.doc_name + "_train_output.json"
        proc = Popen([self.simsinter_exe, self.simsinter_config, train_input, train_output], stdin=PIPE, stdout=PIPE)
        stddata = proc.communicate('\n')    # enter key input required to exit the ConsoleSinter.exe command
        print stddata[0]
        self.acm_result_ramp_train = self.get_acm_simulation_result(train_output)
        self.acm_result_train = self.filter_ramp_steps(self.acm_result_ramp_train, self.nramp_steps_train)
        self.shift_output_data(self.acm_result_train)

    def run_acm_validation(self):
        self.prepare_input_json_for_validation()
        valid_input = self.doc_name + "_valid_input.json"
        valid_output = self.doc_name + "_valid_output.json"
        proc = Popen([self.simsinter_exe, self.simsinter_config, valid_input, valid_output], stdin=PIPE, stdout=PIPE)
        stddata = proc.communicate('\n')    # enter key input required to exit the ConsoleSinter.exe command
        print stddata[0]
        self.acm_result_ramp_valid = self.get_acm_simulation_result(valid_output)
        self.acm_result_valid = self.filter_ramp_steps(self.acm_result_ramp_valid, self.nramp_steps_valid)
        self.shift_output_data(self.acm_result_valid)

    def get_acm_simulation_result(self, file_name):
        with open(file_name, 'r') as fin:
            dict_data = json.load(fin)
        acm_result = []
        for item in self.input_list_all:
            var_array = dict_data[0]['inputs'][item.key_sinter]['value']
            acm_result.append(var_array)
        for item in self.output_list_all:
            var_array = dict_data[0]['outputs'][item.key_sinter]['value']
            acm_result.append(var_array)
        return acm_result

    def filter_ramp_steps(self, acm_result_ramp, nramp_steps):
        ninout = len(acm_result_ramp)
        npair_ramp = len(acm_result_ramp[0])
        npair = npair_ramp - sum(nramp_steps)
        if not npair == len(nramp_steps):
            print 'npair does not match'
        acm_result = [None]*ninout
        for i in xrange(ninout):
            acm_result[i] = [None]*npair
            k = 0
            acm_result[i][0] = acm_result_ramp[i][0]
            for j in xrange(1,npair):
                k += nramp_steps[j] + 1
                acm_result[i][j] = acm_result_ramp[i][k]
        return acm_result
    
    def shift_output_data(self, acm_result):
        # manually shift output one step downward to match the old D-RM Builder results
        npair = len(acm_result[0])
        nin = len(self.input_list_all)
        nout = len(self.output_list_all)
        for i in xrange(nout):
            i1 = i + nin
            for j in xrange(npair-1):
                j1 = npair -1 - j
                acm_result[i1][j1] = acm_result[i1][j1-1]

    def get_varied_data_from_acm_result(self, acm_result):
        varied_data = []
        i = 0
        for item in self.input_list_all:
            if item.bvaried is True:
                varied_data.append(acm_result[i])
            i += 1
        for item in self.output_list_all:
            if item.bvaried is True:
                varied_data.append(acm_result[i])
            i += 1
        return varied_data

    def generate_drm(self):
        ninput = len(self.input_list_sel)
        noutput = len(self.output_list_sel)
        npair = len(self.acm_result_train[0])
        varied_data_train = self.get_varied_data_from_acm_result(self.acm_result_train)
        varied_data_train_t = tuple(list(chain.from_iterable(varied_data_train)))
        drm_opt = []
        if self.imodel_type==1:
            drm_opt.append(self.narma_input.nhistory)
            drm_opt.append(self.narma_input.nneuron_hid)
            drm_opt.append(self.narma_input.nmax_iter_bp)
        else:
            drm_opt.append(self.dabnet_input.itrain_lag_opt)
            drm_opt.append(self.dabnet_input.itrain_red_opt)
            if self.dabnet_input.itrain_lag_opt==1:
                drm_opt.append(self.dabnet_input.nmax_iter_ipopt_lag)
            else:
                drm_opt.append(self.dabnet_input.nmax_iter_bp_lag)
            if self.dabnet_input.itrain_red_opt==1:
                drm_opt.append(self.dabnet_input.nmax_iter_ipopt_red)
            else:
                drm_opt.append(self.dabnet_input.nmax_iter_bp_red)
            drm_opt.append(self.dabnet_input.weight_init)
            drm_opt.append(tuple(self.dabnet_input.ilinear_ann))
            drm_opt.append(tuple(self.dabnet_input.ipole_opt))
            drm_opt.append(tuple(self.dabnet_input.nneuron_hid))
            ipole2_list = [num for elem in self.dabnet_input.ipole2_list for num in elem]
            drm_opt.append(tuple(ipole2_list))
            ndelay_list = [num for elem in self.dabnet_input.ndelay_list for num in elem]
            drm_opt.append(tuple(ndelay_list))
            norder_list = [num for elem in self.dabnet_input.norder_list for num in elem]
            drm_opt.append(tuple(norder_list))
            norder2_list = [num for elem in self.dabnet_input.norder2_list for num in elem]
            drm_opt.append(tuple(norder2_list))
            pole_list = [num for elem in self.dabnet_input.pole_list for num in elem]
            drm_opt.append(tuple(pole_list))
            pole2_list = [num for elem in self.dabnet_input.pole2_list for num in elem]
            drm_opt.append(tuple(pole2_list))
        drm_opt_t = tuple(drm_opt)
        rst = DRMTraining.generate_drm(self.imodel_type, ninput, noutput, npair, varied_data_train_t, drm_opt_t)
        if self.drm_container is None:
            self.drm_container = DRMContainer()
        self.drm_container.set_from_tuple(rst)
        # optimized pole values
        if self.imodel_type==0:
            pole_list = rst[1][9]
            for i in xrange(noutput):
                for j in xrange(ninput):
                    self.dabnet_input.pole_list[i][j] = pole_list[(i*ninput+j)*2]
                    self.dabnet_input.pole2_list[i][j] = pole_list[(i*ninput+j)*2+1]

    def predict_train(self):
        varied_data = self.get_varied_data_from_acm_result(self.acm_result_train)
        if self.imodel_type == 0:   # DABNet
            self.drm_prediction_train = self.drm_container.predict_dabnet(varied_data, self.ipredict_opt_dabnet)
        else:                       # NARMA
            self.drm_prediction_train = self.drm_container.predict_narma(varied_data, self.ipredict_opt_narma)
        # calculate rsquared_train
        self.rsquared_train = self.calc_r2(self.acm_result_train, self.drm_prediction_train)

    def predict_valid(self):
        varied_data = self.get_varied_data_from_acm_result(self.acm_result_valid)
        if self.imodel_type == 0:   # DABNet
            self.drm_prediction_valid = self.drm_container.predict_dabnet(varied_data, self.ipredict_opt_dabnet)
        else:                       # NARMA
            self.drm_prediction_valid = self.drm_container.predict_narma(varied_data, self.ipredict_opt_narma)
        # calculate rsquared_valid
        self.rsquared_valid = self.calc_r2(self.acm_result_valid, self.drm_prediction_valid)

    def calc_r2(self, acm_result, drm_result):
        npair = len(acm_result[0])
        noutput_all = len(self.output_list_all)
        noutput_sel = len(self.output_list_sel)
        ninput_all = len(self.input_list_all)
        ioutput_sel2all = [None]*noutput_sel
        j = 0
        for i in xrange(noutput_all):
            if self.output_list_all[i].bvaried:
                ioutput_sel2all[j] = i
                j += 1
        r2 = [None]*noutput_sel
        for i in xrange(noutput_sel):
            iacm = ninput_all + ioutput_sel2all[i]
            ybar = 0
            for j in xrange(npair):
                ybar += acm_result[iacm][j]
            ybar /= npair
            sst = 0
            sse = 0
            for j in xrange(npair):
                dy = acm_result[iacm][j] - ybar
                sst += dy*dy
                dy = acm_result[iacm][j] - drm_result[i][j]
                sse += dy*dy
            r2[i] = 1 - sse/sst
        return r2

    def perform_uq_analysis(self):
        varied_data = self.get_varied_data_from_acm_result(self.acm_result_valid)
        self.ukf_observation_valid, self.ukf_prediction_valid, self.ukf_std_valid, self.cov_state, self.cov_output = self.drm_container.perform_uq_analysis(varied_data, self.uq_input)
        self.rsquared_valid_ukf = self.calc_r2(self.acm_result_valid, self.ukf_prediction_valid)
