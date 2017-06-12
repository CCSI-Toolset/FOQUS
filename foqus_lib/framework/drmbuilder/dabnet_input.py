# dabnet_input.py

class DABNetInput(object):
    def __init__(self, ninput_init=1, noutput_init=1):
        # number of inputs and outputs
        self.ninput = ninput_init
        self.noutput = noutput_init
        # prediction option: 0=Laguerre, 1=balanced
        self.ipredict_opt = 1
        # internal scaling options, not exposed to GUI
        self.iscale_lag_opt = 0
        self.iscale_red_opt = 1
        # training options: 0=BP, 1=OPOPT
        self.itrain_lag_opt = 0
        self.itrain_red_opt = 0
        # initial weight of Laguerre neural network
        self.weight_init = 0.01
        # maximum iterations
        self.nmax_iter_ipopt_lag = 3000
        self.nmax_iter_ipopt_red = 6000
        self.nmax_iter_bp_lag = 5000
        self.nmax_iter_bp_red = 10000
        # linear model flag, pole optimization option and number of hidden neurons for each output
        self.ilinear_ann = list()
        self.ipole_opt = list()
        self.nneuron_hid = list()
        for i in xrange(self.noutput):
            self.ilinear_ann.append(0)
            self.ipole_opt.append(0)
            self.nneuron_hid.append(10)
        # 2-pole flag, number of delays, Laguerre orders and pole values for each output/input pair
        self.ipole2_list = list()
        self.ndelay_list = list()
        self.norder_list = list()
        self.norder2_list = list()
        self.pole_list = list()
        self.pole2_list = list()
        for i in xrange(self.noutput):
            ipole2s = list()	#flag indicating if use 2-pole option
            ndelays = list()	#number of delays
            norders = list()	#first pole order, including delay
            norders2 = list()	#second pole order, including delay
            poles = list()	#first poles
            poles2 = list()	#second poles
            for j in xrange(self.ninput):
                ipole2s.append(0)
                ndelays.append(0)
                norders.append(6)
                norders2.append(6)
                poles.append(0.5)
                poles2.append(0.95)
            self.ipole2_list.append(ipole2s)
            self.ndelay_list.append(ndelays)
            self.norder_list.append(norders)
            self.norder2_list.append(norders2)
            self.pole_list.append(poles)
            self.pole2_list.append(poles2)

    def set_numbers_of_input_and_output(self, ninput_, noutput_):
        self.ninput = ninput_
        self.noutput = noutput_
        del self.ilinear_ann[:]
        del self.ipole_opt[:]
        del self.nneuron_hid[:]
        del self.ipole2_list[:]
        del self.ndelay_list[:]
        del self.norder_list[:]
        del self.norder2_list[:]
        del self.pole_list[:]
        del self.pole2_list[:]
        for i in xrange(self.noutput):
            self.ilinear_ann.append(0)
            self.ipole_opt.append(0)
            self.nneuron_hid.append(10)
            ipole2s = list()
            ndelays = list()
            norders = list()
            norders2 = list()
            poles = list()
            poles2 = list()
            for j in xrange(self.ninput):
                ipole2s.append(0)
                ndelays.append(0)
                norders.append(6)
                norders2.append(6)
                poles.append(0.5)
                poles2.append(0.95)
            self.ipole2_list.append(ipole2s)
            self.ndelay_list.append(ndelays)
            self.norder_list.append(norders)
            self.norder2_list.append(norders2)
            self.pole_list.append(poles)
            self.pole2_list.append(poles2)

    def set_to_default_values(self):
        # prediction option: 0=Laguerre, 1=balanced
        self.ipredict_opt = 1
        # internal scaling options, not exposed to GUI
        self.iscale_lag_opt = 0
        self.iscale_red_opt = 1
        # training options: 0=BP, 1=OPOPT
        self.itrain_lag_opt = 0
        self.itrain_red_opt = 0
        # initial weight of Laguerre neural network
        self.weight_init = 0.01
        # maximum iterations
        self.nmax_iter_ipopt_lag = 3000
        self.nmax_iter_ipopt_red = 6000
        self.nmax_iter_bp_lag = 5000
        self.nmax_iter_bp_red = 10000
        # pole optimization option and number of hidden neurons for each output
        for i in xrange(self.noutput):
            self.ilinear_ann[i] = 0
            self.ipole_opt[i] = 0
            self.nneuron_hid[i] = 10
        # Laguerre orders and pole values for each output/input pair
        for i in xrange(self.noutput):
            for j in xrange(self.ninput):
                self.ipole2_list[i][j] = 0
                self.ndelay_list[i][j] = 0
                self.norder_list[i][j] = 6
                self.norder2_list[i][j] = 6
                self.pole_list[i][j] = 0.5
                self.pole2_list[i][j] = 0.95

    def to_dictionary(self):
        dict_data = dict()
        dict_data['ninput'] = self.ninput
        dict_data['noutput'] = self.noutput
        dict_data['ipredict_opt'] =self.ipredict_opt
        dict_data['iscale_lag_opt'] = self.iscale_lag_opt
        dict_data['iscale_red_opt'] = self.iscale_red_opt
        dict_data['itrain_lag_opt'] = self.itrain_lag_opt
        dict_data['itrain_red_opt'] = self.itrain_red_opt
        dict_data['weight_init'] = self.weight_init
        dict_data['nmax_iter_ipopt_lag'] = self.nmax_iter_ipopt_lag
        dict_data['nmax_iter_ipopt_red'] = self.nmax_iter_ipopt_red
        dict_data['nmax_iter_bp_lag'] = self.nmax_iter_bp_lag
        dict_data['nmax_iter_bp_red'] = self.nmax_iter_bp_red
        dict_data['ilinear_ann'] = self.ilinear_ann
        dict_data['ipole_opt'] = self.ipole_opt
        dict_data['nneuron_hid'] = self.nneuron_hid
        dict_data['ipole2_list'] = self.ipole2_list
        dict_data['ndelay_list'] = self.ndelay_list
        dict_data['norder_list'] = self.norder_list
        dict_data['norder2_list'] = self.norder2_list
        dict_data['pole_list'] = self.pole_list
        dict_data['pole2_list'] = self.pole2_list
        return dict_data

    def from_dictionary(self, dict_data):
        self.ninput = dict_data['ninput']
        self.noutput = dict_data['noutput']
        self.set_numbers_of_input_and_output(self.ninput, self.noutput)
        self.ipredict_opt = dict_data['ipredict_opt']
        self.iscale_lag_opt = dict_data['iscale_lag_opt']
        self.iscale_red_opt = dict_data['iscale_red_opt']
        self.itrain_lag_opt = dict_data['itrain_lag_opt']
        self.itrain_red_opt = dict_data['itrain_red_opt']
        self.weight_init = dict_data['weight_init']
        self.nmax_iter_ipopt_lag = dict_data['nmax_iter_ipopt_lag']
        self.nmax_iter_ipopt_red = dict_data['nmax_iter_ipopt_red']
        self.nmax_iter_bp_lag = dict_data['nmax_iter_bp_lag']
        self.nmax_iter_bp_red = dict_data['nmax_iter_bp_red']
        self.ilinear_ann = dict_data['ilinear_ann']
        self.ipole_opt = dict_data['ipole_opt']
        self.nneuron_hid = dict_data['nneuron_hid']
        self.ipole2_list = dict_data['ipole2_list']
        self.ndelay_list = dict_data['ndelay_list']
        self.norder_list = dict_data['norder_list']
        self.norder2_list = dict_data['norder2_list']
        self.pole_list = dict_data['pole_list']
        self.pole2_list = dict_data['pole2_list']

