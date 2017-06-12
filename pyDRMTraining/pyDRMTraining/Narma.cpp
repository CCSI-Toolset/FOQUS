//Narma.cpp
#include <math.h>
#include "Narma.h"

CNarma::CNarma(void)
{
	ipredict_opt = 0;
	ninput = 1;
	noutput = 1;
	nhistory = 2;
	nneuron_hid = 10;
	nmax_iter_bp = 10000;
}

CNarma::~CNarma(void)
{
}

void CNarma::ProcessIdentificationDataForTraining()
{
	//assuming data in pid_data has already been scaled and contains only modeled input and output variables
	int i, j, k, n, m;
	int npoint = pid_data->npair;
	ann_data.SetSize(npoint, (ninput+noutput)*nhistory, noutput);
	double** ppdata_id = pid_data->ppdata;
	double** ppdata_ann = ann_data.ppdata;
	double* prow_id;
	double* prow_ann;
	//for the first few points, use the steady state values for history data
	for (i=0; i<npoint; i++)
	{
		prow_id = ppdata_id[i];
		prow_ann = ppdata_ann[i];
		n = 0;
		//inputs from history u
		for (j=0; j<ninput; j++)
		{
			for (k=0; k<nhistory; k++)
			{
				m = i-nhistory+k;
				if (m<0)
					m = 0;
				prow_ann[n++] = ppdata_id[m][j];
			}
		}
		//outputs from history y
		for (j=0; j<noutput; j++)
		{
			for (k=0; k<nhistory; k++)
			{
				m = i-nhistory+k;
				if (m<0)
					m = 0;
				prow_ann[n++] = ppdata_id[m][ninput+j];
			}
		}
		//outputs results
		for (j=0; j<noutput; j++)
			prow_ann[n++] = prow_id[ninput+j];
	}
}

void CNarma::TrainNeuralNetwork()
{
	int nhidden_layer = 1;
	int pnneuron_hid[1];
	pnneuron_hid[0] = nneuron_hid;
	ann.SetNetworkStructure(nhistory*(ninput+noutput),noutput,nhidden_layer,pnneuron_hid);
	ann.SetRandomSeed(0);
	ann.SetTrainMethod(1);
	ann.SetStopError(0.00001);
	//currently based on BP training
	ann.SetMaximumNumberOfEpoches(nmax_iter_bp);
	//input and output have been scaled, no need to scale again
	ann.TrainDataSet(ann_data.npair,ann_data.ppdata);
}

void CNarma::PredictByDRM(int np, double** ppin, double** ppout)
{
	//np: the number of the data points
	//ppin: the 2-D array of input and output data, ppdata in vd_data can be used for prediction, currently use history output data from high-fidelity model
	//ppout: the 2-D array of output data without unscaling
	int i, j, k, n, m;
	double* prow;
	double* pann_input = new double [nhistory*(ninput+noutput)];
	if (ipredict_opt)		//use D-RM prediction for history data
	{
		//copy initial history data to ppout
		for (j=0; j<noutput; j++)
			ppout[0][j] = ppin[0][ninput+j];
	}
	for (i=0; i<np; i++)
	{
		prow = ppin[i];
		n = 0;
		for (j=0; j<ninput; j++)
		{
			for (k=0; k<nhistory; k++)
			{
				m = i-nhistory+k;
				if (m<0)
					m = 0;
				pann_input[n++] = ppin[m][j];
			}
		}
		if (ipredict_opt)	//use D-RM prediction for history data
		{
			for (j=0; j<noutput; j++)
			{
				for (k=0; k<nhistory; k++)
				{
					m = i-nhistory+k;
					if (m<0)
						m = 0;
					pann_input[n++] = ppout[m][j];
				}
			}
		}
		else
		{
			for (j=0; j<noutput; j++)
			{
				for (k=0; k<nhistory; k++)
				{
					m = i-nhistory+k;
					if (m<0)
						m = 0;
					pann_input[n++] = ppin[m][ninput+j];
				}
			}
		}
		ann.Predict(pann_input,ppout[i]);
	}
	delete [] pann_input;
}

void CNarma::WriteDRMTextFile(FILE* pf)
{
	fprintf(pf,"//neural network data\n");
	ann.WriteANNData(pf);
}

void CNarma::WriteDRMMatlabFile(FILE* pf)
{
	fprintf(pf,"nhistory = %d;\n",nhistory);
	ann.WriteANNMatlabFile(pf);
}

PyObject* CNarma::GetNarmaAsTuple()
{
	PyObject* obj_ann = ann.GetAnnAsTuple();
	PyObject* obj_result = PyTuple_New(4);
	PyTuple_SetItem(obj_result, 0, Py_BuildValue("i", ninput));
	PyTuple_SetItem(obj_result, 1, Py_BuildValue("i", noutput));
	PyTuple_SetItem(obj_result, 2, Py_BuildValue("i", nhistory));
	PyTuple_SetItem(obj_result, 3, Py_BuildValue("O", obj_ann));
	return obj_result;
}