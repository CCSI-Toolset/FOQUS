#include "SolverInput.h"
#include "Python.h"

static PyObject* db_desc(PyObject *self, PyObject *args)
{
	printf("DRM Sampling Python Binding version 1.0\nFunctions in the module:\ndesc()\nsample_input_space(step_change_input)\n");
	Py_INCREF(Py_None);
	return Py_None;
	//the two lines above can be replaced by a macro py_RETURN_NONE
}

static PyObject* db_sample_input_space(PyObject* self, PyObject* args)
{
	//args: function argument is a tuple of integer values and 5 tuples
	CSolverInput si;					//an instance of CSolverInput
	double rand_seed;					//seed for random number generator
	int i;
	int	ndim;							//dimension: number of varied input variables
	int ireverse;						//1 if reverse step changes are included
	int npoint;							//number of LHS points
	int nduration;						//number of durations
	int duration0;						//initial duration, the number of sampling time steps
	int len_seq;						//length of sequence
	int nresult;						//number of double values in returned step change sequence
	PyObject* seq;						//sequence object
	PyObject* item;						//an object
	PyObject* obj_vduration;			//duration vector tuple
	PyObject* obj_vbvaried;				//bvariad vector tuple
	PyObject* obj_vxdefault;			//xdefault vector tuple
	PyObject* obj_vxlower;				//xlower vector tuple
	PyObject* obj_vxupper;				//xupper vector
	PyObject* obj_result;				//result tuple to return

	if (!PyArg_ParseTuple(args, "diiiiiOOOOO", &rand_seed, &ndim, &ireverse, &npoint, &nduration, &duration0, &obj_vduration, &obj_vbvaried, &obj_vxdefault, &obj_vxlower, &obj_vxupper))
		return NULL;
	//get duration vector
	seq = PySequence_Fast(obj_vduration, "expect a sequence");
	if (!seq)
		return NULL;
	len_seq = PySequence_Size(obj_vduration);
	if (len_seq<0)
		return NULL;
	if (len_seq!=nduration)
		return NULL;
	for (i=0; i<len_seq; i++)
	{
		item = PySequence_Fast_GET_ITEM(seq,i);
		si.vduration.push_back(PyInt_AsLong(item));
	}
	Py_DECREF(seq);
	//get bvaried vector
	seq = PySequence_Fast(obj_vbvaried, "expect a sequence");
	if (!seq)
		return NULL;
	len_seq = PySequence_Size(obj_vbvaried);
	if (len_seq<0)
		return NULL;
	for (i=0; i<len_seq; i++)
	{
		item = PySequence_Fast_GET_ITEM(seq,i);
		if (item==Py_True)
			si.vbvaried.push_back(true);
		else
			si.vbvaried.push_back(false);
	}
	Py_DECREF(seq);
	//get xdefault vector
	seq = PySequence_Fast(obj_vxdefault, "expect a sequence");
	if (!seq)
		return NULL;
	len_seq = PySequence_Size(obj_vxdefault);
	if (len_seq<0)
		return NULL;
	for (i=0; i<len_seq; i++)
	{
		item = PySequence_Fast_GET_ITEM(seq,i);
		si.vxdefault.push_back(PyFloat_AsDouble(item));
	}
	Py_DECREF(seq);
	//get xlower vector
	seq = PySequence_Fast(obj_vxlower, "expect a sequence");
	if (!seq)
		return NULL;
	len_seq = PySequence_Size(obj_vxlower);
	if (len_seq<0)
		return NULL;
	for (i=0; i<len_seq; i++)
	{
		item = PySequence_Fast_GET_ITEM(seq,i);
		si.vxlower.push_back(PyFloat_AsDouble(item));
	}
	Py_DECREF(seq);
	//get xupper vector
	seq = PySequence_Fast(obj_vxupper, "expect a sequence");
	if (!seq)
		return NULL;
	len_seq = PySequence_Size(obj_vxupper);
	if (len_seq<0)
		return NULL;
	for (i=0; i<len_seq; i++)
	{
		item = PySequence_Fast_GET_ITEM(seq,i);
		si.vxupper.push_back(PyFloat_AsDouble(item));
	}
	Py_DECREF(seq);
	//make sure the ndim is consistant with v
	//prepare the si object
	si.EnableReverse(ireverse);
	si.SetDimension(ndim);
	si.SetNumberOfPoints(npoint);
	si.SetNumberOfDurations(nduration);
	si.SetInitialDuration(duration0);
	if (!si.CheckVariedInputDimension())		//check if vbvaried contains ndim true values
		return NULL;
	srand(rand_seed);
	si.GenerateTrainingSequence();
	si.PrepareSequenceVectorForACMInputArray();
	//build result tuple
	nresult = si.vsequence.size();
	obj_result = PyTuple_New(nresult);
	for (i=0; i<nresult; i++)
		PyTuple_SetItem(obj_result, i, Py_BuildValue("d", si.vsequence[i]));
	return obj_result;
}

static PyMethodDef db_methods[] = {
	{"desc", db_desc, METH_VARARGS, "desc() DRM Sampling description"},
	{"sample_input_space", db_sample_input_space, METH_VARARGS, "sample_input_space() generate step change sequence after sampling input space"},
	{NULL, NULL, 0, NULL}	//last line is a sentinel with NULL
};

//name of the function has to be "initxxx" where "xxx" is the name of the project
PyMODINIT_FUNC initpyDRMSampling(void)
{
	//first parameter has to be a string that is the name of the project
	Py_InitModule("pyDRMSampling", db_methods);
}
