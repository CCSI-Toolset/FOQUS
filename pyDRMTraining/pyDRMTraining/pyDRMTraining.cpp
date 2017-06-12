#include "DRMContainer.h"
//#include "Python.h"

static PyObject* db_desc(PyObject *self, PyObject *args)
{
	printf("DRM Generation Python Binding version 1.0\nFunctions in the module:\ndesc()\ngenerate_drm(drm_input)\n");
	Py_INCREF(Py_None);
	return Py_None;
	//the two lines above can be replaced by a macro py_RETURN_NONE
}

static PyObject* db_generate_drm(PyObject* self, PyObject* args)
{
	int i, j, k;
	int imodel_type;					//model type, 0=DABNet, 1=NARMA
	int ninput;							//number of varied input parameters
	int noutput;						//number of varied output parameters
	int npair;							//number of pairs of training data
	int len_seq;						//sequence length
	int nhistory;						//number of history point in NARMA model
	int nneuron_hid;					//number of neurons in hidden layer in NARMA model
	int nmax_iter;						//maximum number of iterations for NARMA model
	int itrain_lag_opt;					//training option for Laguerre DABNet model
	int itrain_red_opt;					//training option for reduced DABNet model
	int nmax_iter_lag;					//maximum number of iterations for Laguerre DABNet model
	int nmax_iter_red;					//maximum number of iterations for reduced DABNet model
	double weight_init;					//initial weight in the ANN of Laguerre DABNet model
	double x;							//a double variable
	double** ppdata;					//pointer to training data
	CDRMContainer drmct;				//a DRMCountainer object used for training the DRM
	PyObject* seq;						//sequence object
	PyObject* item;						//an Python object
	PyObject* obj_td;					//training data tuple, size=npair*(ninput+noutput)
	PyObject* obj_drm_opt;				//optional DRM input parameter tuple
	PyObject* obj_ilinear_ann;			//linear model flag
	PyObject* obj_ipole_opt;			//pole value specification option tuple, 0=user specified, 1=optimized, size=noutput
	PyObject* obj_nneuron_hid;			//number of hidden neurons tuple, size=noutput
	PyObject* obj_ipole2_list;			//2-pole flag
	PyObject* obj_ndelay_list;			//number of delays
	PyObject* obj_norder_list;			//Laguerre order tuple, size=noutput*ninput
	PyObject* obj_norder2_list;			//2nd Laguerre order tuple, size=noutput*ninput
	PyObject* obj_pole_list;			//pole value tuple, size=noutput*ninput
	PyObject* obj_pole2_list;			//2nd pole value tuple, size=noutput*ninput
	if (!PyArg_ParseTuple(args, "iiiiOO", &imodel_type, &ninput, &noutput, &npair, &obj_td, &obj_drm_opt))
		return NULL;
	drmct.SetModelType(imodel_type);
	drmct.SetNumberOfInputs(ninput);
	drmct.SetNumberOfOutputs(noutput);
	//get the training data, assuming pair major order (parameter after parameter)
	seq = PySequence_Fast(obj_td, "expect a training data vector");
	if (!seq)
		return NULL;
	len_seq = PySequence_Size(obj_td);
	if (len_seq<0)
		return NULL;
	if (len_seq!=npair*(ninput+noutput))
		return NULL;
	drmct.data_varied.SetSize(npair, ninput, noutput);
	ppdata = drmct.data_varied.ppdata;
	k = 0;
	for (i=0; i<ninput+noutput; i++)
	{
		for (j=0; j<npair; j++)
		{
			item = PySequence_Fast_GET_ITEM(seq,k);
			x = PyFloat_AsDouble(item);
			ppdata[j][i] = x;
			k++;
		}
	}
	Py_DECREF(seq);
	//get optional DRM input parameters
	if (imodel_type)	//NARMA model
	{
		if (!PyArg_ParseTuple(obj_drm_opt, "iii", &nhistory, &nneuron_hid, &nmax_iter))
			return NULL;
		drmct.InitNarma();
		drmct.drm_narma.nhistory = nhistory;
		drmct.drm_narma.nneuron_hid = nneuron_hid;
		drmct.drm_narma.nmax_iter_bp = nmax_iter;
	}
	else      //DABNet model
	{
		drmct.InitDabnet();				
		if (!PyArg_ParseTuple(obj_drm_opt, "iiiidOOOOOOOOO", &itrain_lag_opt, &itrain_red_opt, &nmax_iter_lag, &nmax_iter_red, &weight_init, &obj_ilinear_ann, &obj_ipole_opt, &obj_nneuron_hid, &obj_ipole2_list, &obj_ndelay_list, &obj_norder_list, &obj_norder2_list, &obj_pole_list, &obj_pole2_list))
			return NULL;
		drmct.dabnet_input.itrain_lag_opt = itrain_lag_opt;
		drmct.dabnet_input.itrain_red_opt = itrain_red_opt;
		if (itrain_lag_opt)
			drmct.dabnet_input.nmax_iter_ipopt_lag = nmax_iter_lag;
		else
			drmct.dabnet_input.nmax_iter_bp_lag = nmax_iter_lag;
		if (itrain_red_opt)
			drmct.dabnet_input.nmax_iter_ipopt_red = nmax_iter_red;
		else
			drmct.dabnet_input.nmax_iter_bp_red = nmax_iter_red;
		drmct.dabnet_input.weight_init = weight_init;
		//obj_ilinear_ann vector
		seq = PySequence_Fast(obj_ilinear_ann, "expect a sequence of linear model flag options");
		if (!seq)
			return NULL;
		len_seq = PySequence_Size(obj_ilinear_ann);
		if (len_seq<0)
			return NULL;
		if (len_seq!=noutput)
			return NULL;
		for (i=0; i<len_seq; i++)
		{
			item = PySequence_Fast_GET_ITEM(seq,i);
			drmct.drm_dabnet[i].ilinear_ann = PyInt_AsLong(item);
		}
		Py_DECREF(seq);
		//obj_ipole_opt vector
		seq = PySequence_Fast(obj_ipole_opt, "expect a sequence of pole value options");
		if (!seq)
			return NULL;
		len_seq = PySequence_Size(obj_ipole_opt);
		if (len_seq<0)
			return NULL;
		if (len_seq!=noutput)
			return NULL;
		for (i=0; i<len_seq; i++)
		{
			item = PySequence_Fast_GET_ITEM(seq,i);
			drmct.drm_dabnet[i].ipole_opt = PyInt_AsLong(item);
		}
		Py_DECREF(seq);
		//obj_nneuron_hid vector
		seq = PySequence_Fast(obj_nneuron_hid, "expect a sequence of numbers of neurons");
		if (!seq)
			return NULL;
		len_seq = PySequence_Size(obj_nneuron_hid);
		if (len_seq<0)
			return NULL;
		if (len_seq!=noutput)
			return NULL;
		for (i=0; i<len_seq; i++)
		{
			item = PySequence_Fast_GET_ITEM(seq,i);
			drmct.drm_dabnet[i].nneuron_hid = PyInt_AsLong(item);
		}
		Py_DECREF(seq);
		//2-D vector obj_ipole2_list flag vector
		seq = PySequence_Fast(obj_ipole2_list, "expect a sequence of 2-pole flags");
		if (!seq)
			return NULL;
		len_seq = PySequence_Size(obj_ipole2_list);
		if (len_seq<0)
			return NULL;
		if (len_seq!=noutput*ninput)
			return NULL;
		k = 0;
		for (i=0; i<noutput; i++)
		{
			for (j=0; j<ninput; j++)
			{
				item = PySequence_Fast_GET_ITEM(seq,k);
				drmct.drm_dabnet[i].ipole2_list[j] = PyInt_AsLong(item);
				k++;
			}
		}
		Py_DECREF(seq);
		//2-D vector obj_ndelay_list vector
		seq = PySequence_Fast(obj_ndelay_list, "expect a sequence of number of delays");
		if (!seq)
			return NULL;
		len_seq = PySequence_Size(obj_ndelay_list);
		if (len_seq<0)
			return NULL;
		if (len_seq!=noutput*ninput)
			return NULL;
		k = 0;
		for (i=0; i<noutput; i++)
		{
			for (j=0; j<ninput; j++)
			{
				item = PySequence_Fast_GET_ITEM(seq,k);
				drmct.drm_dabnet[i].ndelay_list[j] = PyInt_AsLong(item);
				k++;
			}
		}
		Py_DECREF(seq);
		//2-D vector obj_norder_list
		seq = PySequence_Fast(obj_norder_list, "expect a sequence of Laguerre orders");
		if (!seq)
			return NULL;
		len_seq = PySequence_Size(obj_norder_list);
		if (len_seq<0)
			return NULL;
		if (len_seq!=noutput*ninput)
			return NULL;
		k = 0;
		for (i=0; i<noutput; i++)
		{
			for (j=0; j<ninput; j++)
			{
				item = PySequence_Fast_GET_ITEM(seq,k);
				drmct.drm_dabnet[i].norder_list[j] = PyInt_AsLong(item);
				k++;
			}
		}
		Py_DECREF(seq);
		//2-D vector obj_norder2_list
		seq = PySequence_Fast(obj_norder2_list, "expect a sequence of 2nd Laguerre orders");
		if (!seq)
			return NULL;
		len_seq = PySequence_Size(obj_norder2_list);
		if (len_seq<0)
			return NULL;
		if (len_seq!=noutput*ninput)
			return NULL;
		k = 0;
		for (i=0; i<noutput; i++)
		{
			for (j=0; j<ninput; j++)
			{
				item = PySequence_Fast_GET_ITEM(seq,k);
				drmct.drm_dabnet[i].norder2_list[j] = PyInt_AsLong(item);
				k++;
			}
		}
		Py_DECREF(seq);
		//2-D vector obj_pole_list
		seq = PySequence_Fast(obj_pole_list, "expect a sequence of pole values");
		if (!seq)
			return NULL;
		len_seq = PySequence_Size(obj_pole_list);
		if (len_seq<0)
			return NULL;
		if (len_seq!=noutput*ninput)
			return NULL;
		k = 0;
		for (i=0; i<noutput; i++)
		{
			for (j=0; j<ninput; j++)
			{
				item = PySequence_Fast_GET_ITEM(seq,k);
				drmct.drm_dabnet[i].pole_list[j] = PyFloat_AsDouble(item);
				k++;
			}
		}
		Py_DECREF(seq);
		//2-D vector obj_pole2_list
		seq = PySequence_Fast(obj_pole2_list, "expect a sequence of 2nd pole values");
		if (!seq)
			return NULL;
		len_seq = PySequence_Size(obj_pole2_list);
		if (len_seq<0)
			return NULL;
		if (len_seq!=noutput*ninput)
			return NULL;
		k = 0;
		for (i=0; i<noutput; i++)
		{
			for (j=0; j<ninput; j++)
			{
				item = PySequence_Fast_GET_ITEM(seq,k);
				drmct.drm_dabnet[i].pole2_list[j] = PyFloat_AsDouble(item);
				k++;
			}
		}
		Py_DECREF(seq);
	}
	//finally generate DRM, this call is CPU-intensive
	//needs to provide a window to show progress
	drmct.GenerateDRM();
	drmct.CalcMeanAndSigmaOfReducedModelStateVariables();
	//return DRM data as a tuple
	return drmct.GetDRMAsTuple();
}

static PyMethodDef db_methods[] = {
	{"desc", db_desc, METH_VARARGS, "desc() DRM generation description"},
	{"generate_drm", db_generate_drm, METH_VARARGS, "generate_drm() generates DRM given training data and DRM options"},
	{NULL, NULL, 0, NULL}	//last line is a sentinel with NULL
};

//name of the function has to be "initxxx" where "xxx" is the name of the project
PyMODINIT_FUNC initpyDRMTraining(void)
{
	//first parameter has to be a string that is the name of the project
	Py_InitModule("pyDRMTraining", db_methods);
}
