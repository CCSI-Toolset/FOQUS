//Dabnet.cpp
#include <math.h>
#include "Dabnet.h"
#include "IpIpoptApplication.hpp"
#include "AnnIpopt.h"

using namespace Ipopt;

CDabnet::CDabnet(void)
{
	ninput = 1;
	noutput = 1;
	ioutput = 0;
	ipole_opt = 0;
	nneuron_hid = 10;
	ilinear_ann = 0;
	nstate_lag = 1;
	nstate_red = 1;
	pid_data = NULL;
}

CDabnet::~CDabnet(void)
{
}

void CDabnet::ResizeVectors(int ninput)
{
	ipole2_list.resize(ninput);
	ndelay_list.resize(ninput);
	norder_list.resize(ninput);
	norder2_list.resize(ninput);
	pole_list.resize(ninput);
	pole2_list.resize(ninput);
}

void CDabnet::UpdateTotalLaguerreOrders()
{
	//assume lss_list has been created
	int i;
	nstate_lag = 0;
	for (i=0; i<ninput; i++)
		nstate_lag += lss_list[i].nstate;
}

void CDabnet::CreateLaguerreStateSpaceList()
{
	int i;
	int nstate1;			//first Laguerre order
	lss_list.resize(ninput);
	for (i=0; i<ninput; i++)
	{
		lss_list[i].ipole2 = ipole2_list[i];
		lss_list[i].ndelay = ndelay_list[i];
		lss_list[i].a = pole_list[i];
		lss_list[i].a2 = pole2_list[i];
		nstate1 = norder_list[i];
		lss_list[i].nstate2 = norder2_list[i];
		if (ipole2_list[i])
			lss_list[i].nstate = nstate1 + norder2_list[i];
		else
			lss_list[i].nstate = nstate1;
		lss_list[i].AllocateMemory();
		lss_list[i].CreateUnbalancedStateSpace();
	}
}

void CDabnet::UpdateLaguerreStateSpaceList()
{
	//assume memory already allocated
	int i;
	for (i=0; i<ninput; i++)
	{
		lss_list[i].a = pole_list[i];
		lss_list[i].a2 = pole2_list[i];
		lss_list[i].CreateUnbalancedStateSpace();
	}
}

void CDabnet::ProcessIdentificationDataForLaguerreTraining()
{
	//id_data has already been scaled (both input and output)
	int i, j, k, n;
	int nstate_j;
	int npoint = pid_data->npair;
	ann_data.SetSize(npoint, nstate_lag, noutput);
	double** ppdata_id = pid_data->ppdata;
	double** ppdata_ann = ann_data.ppdata;
	double* prow_id;
	double* prow_ann;
	//calculate the state variables at steady state assuming input for the steady state is the same as the input of the first point
	prow_id = ppdata_id[0];
	for (j=0; j<ninput; j++)
		lss_list[j].InitStateVectorToSteadyState(prow_id[j]);
	//define u(k) as the input value between k and k+1 time interval [k,k+1)
	//note that each row in id_data is a pair of u(k) and y(k+1), the response after u(k) is applied for a fixed time interval
	//the ANN mapping is x(k+1) to y(k+1)
	for (i=0; i<npoint; i++)
	{
		prow_id = ppdata_id[i];
		prow_ann = ppdata_ann[i];
		n = 0;
		//inputs
		for (j=0; j<ninput; j++)
		{
			//lss_list[j].CalcNextStateVector(prow_id[j]);
			nstate_j = lss_list[j].nstate;
			for (k=0; k<nstate_j; k++)
				prow_ann[n++] = lss_list[j].px[k];
			//apply Ax+Bu
			lss_list[j].CalcNextStateVector(prow_id[j]);
		}
		//outputs, note that noutput=1 and ioutput is the index of modeled output variables assigned by CDRMContainer
		prow_ann[n++] = prow_id[ninput+ioutput];
	}
}

void CDabnet::ProcessIdentificationDataForReducedModelTraining()
{
	int i, j, k, n;
	int nstate_j;
	int npoint = pid_data->npair;
	//resize the ann_data, note that nstate_red has been updated by ReduceLaguerreStateSpace()function call
	ann_data.SetSize(npoint, nstate_red, noutput);
	double** ppdata_id = pid_data->ppdata;
	double** ppdata_ann = ann_data.ppdata;
	double* prow_id;
	double* prow_ann;
	//for the first point, calculate the state variables at steady state
	prow_id = ppdata_id[0];
	for (j=0; j<ninput; j++)
		rss_list[j].InitStateVectorToSteadyState(prow_id[j]);
	//define u(k) as the input value between k and k+1 time interval [k,k+1)
	//note that each row in id_data is a pair of u(k) and y(k+1), the response after u(k) is applied for a fixed time interval
	//the ANN mapping is x(k+1) to y(k+1)
	for (i=0; i<npoint; i++)
	{
		prow_id = ppdata_id[i];
		prow_ann = ppdata_ann[i];
		n = 0;
		//inputs
		for (j=0; j<ninput; j++)
		{
			nstate_j = rss_list[j].nstate;
			//rss_list[j].CalcNextStateVector(prow_id[j]);
			for (k=0; k<nstate_j; k++)
				prow_ann[n++] = rss_list[j].px[k];
			rss_list[j].CalcNextStateVector(prow_id[j]);
		}
		//outputs, note that noutput=1 and ioutput is the index of modeled output variables assigned by CDRMContainer
		prow_ann[n++] = prow_id[ninput+ioutput];
	}
}

void CDabnet::TrainLaguerreNeuralNetworkByBackPropagation()
{
	//nn is the number of neurons in hidden layer
	//use default activation function (sigmoid for hidden layer and linear for output layer)
	int nhidden_layer = 1;		//use just one hidden layer
	int pnneuron_hid[1];
	pnneuron_hid[0] = nneuron_hid;
	ann_lag.SetNetworkStructure(nstate_lag,noutput,nhidden_layer,pnneuron_hid);
	ann_lag.InitUniformWeights(pdabnet_input->weight_init);		//use small weights help balanced realization
	ann_lag.SetRandomSeed(0);
	ann_lag.SetTrainMethod(1);
	ann_lag.SetStopError(0.00001);
	ann_lag.SetMaximumNumberOfEpoches(pdabnet_input->nmax_iter_bp_lag);
	if (pdabnet_input->iscale_lag_opt)
	{
		ann_lag.CalcMeanSigmaForInputOutputData(ann_data.npair,ann_data.ppdata);
		ann_lag.ScaleInputOutputData(ann_data.npair,ann_data.ppdata);
	}
	else
		ann_lag.SetDefaultMeanSigma();
	ann_lag.TrainDataSet(ann_data.npair,ann_data.ppdata);
}

void CDabnet::TrainLaguerreNeuralNetworkByIpopt()
{
	int nhidden_layer = 1;		//use just one hidden layer
	int pnneuron_hid[1];
	pnneuron_hid[0] = nneuron_hid;
	ann_lag.SetNetworkStructure(nstate_lag,noutput,nhidden_layer,pnneuron_hid);
	ann_lag.SetWeightForInitialization(pdabnet_input->weight_init);	//to be used by IPOPT initialization function
	if (pdabnet_input->iscale_lag_opt)
	{
		ann_lag.CalcMeanSigmaForInputOutputData(ann_data.npair,ann_data.ppdata);
		ann_lag.ScaleInputOutputData(ann_data.npair,ann_data.ppdata);
	}
	else
		ann_lag.SetDefaultMeanSigma();
	CAnnIpopt* pmynlp = new CAnnIpopt();
	SmartPtr<TNLP> mynlp = pmynlp;
	pmynlp->pann = &ann_lag;
	pmynlp->pdc = &ann_data;
	SmartPtr<IpoptApplication> app = IpoptApplicationFactory();
	app->Options()->SetNumericValue("tol", 1e-5);		//revised from 1e-7
	app->Options()->SetIntegerValue("max_iter", pdabnet_input->nmax_iter_ipopt_lag);
	app->Options()->SetStringValue("mu_strategy", "adaptive");
	app->Options()->SetStringValue("output_file", "ipopt.out");
	app->Options()->SetIntegerValue("print_level", 0);	//minimum print out in DOS window
	ApplicationReturnStatus status;
	//initialization
	status = app->Initialize();
	if (status != Solve_Succeeded)
	{
		printf("Error during initialization!\n");
		return;
	}
	//solve the problem
	status = app->OptimizeTNLP(mynlp);
	//if (status != Solve_Succeeded)
	//	printf("IPOPT failed to reach tolerance of 0.00001.\n");
}

void CDabnet::TrainLaguerreNeuralNetwork()
{
	if (ilinear_ann)	//default type is 2
		ann_lag.SetHiddenLayerActivationType(0);
	if (pdabnet_input->itrain_lag_opt)
		TrainLaguerreNeuralNetworkByIpopt();
	else
		TrainLaguerreNeuralNetworkByBackPropagation();
}

void CDabnet::TrainReducedModelNeuralNetworkByBackPropagation()
{
	int nhidden_layer = 1;
	int pnneuron_hid[1];
	pnneuron_hid[0] = nneuron_hid;
	ann_red.SetNetworkStructure(nstate_red,noutput,nhidden_layer,pnneuron_hid);
	ann_red.SetRandomSeed(0);
	ann_red.SetTrainMethod(1);
	ann_red.SetStopError(0.00001);
	ann_red.SetMaximumNumberOfEpoches(pdabnet_input->nmax_iter_bp_red);
	if (pdabnet_input->iscale_red_opt)
	{
		ann_red.CalcMeanSigmaForInputOutputData(ann_data.npair,ann_data.ppdata);
		ann_red.ScaleInputOutputData(ann_data.npair,ann_data.ppdata);
	}
	else
		ann_red.SetDefaultMeanSigma();
	ann_red.TrainDataSet(ann_data.npair,ann_data.ppdata);	
}

void CDabnet::TrainReducedModelNeuralNetworkByIpopt()
{
	int nhidden_layer = 1;		//use just one hidden layer
	int pnneuron_hid[1];
	pnneuron_hid[0] = nneuron_hid;
	ann_red.SetNetworkStructure(nstate_red,noutput,nhidden_layer,pnneuron_hid);
	ann_red.SetWeightForInitialization(0.2);	//to be used by IPOPT initialization function
	if (pdabnet_input->iscale_red_opt)
	{
		ann_red.CalcMeanSigmaForInputOutputData(ann_data.npair,ann_data.ppdata);
		ann_red.ScaleInputOutputData(ann_data.npair,ann_data.ppdata);
	}
	else
		ann_red.SetDefaultMeanSigma();
	CAnnIpopt* pmynlp = new CAnnIpopt();
	SmartPtr<TNLP> mynlp = pmynlp;
	pmynlp->pann = &ann_red;
	pmynlp->pdc = &ann_data;
	SmartPtr<IpoptApplication> app = IpoptApplicationFactory();
	app->Options()->SetNumericValue("tol", 1e-5);		//revised from 1e-7
	app->Options()->SetIntegerValue("max_iter", pdabnet_input->nmax_iter_ipopt_red);
	app->Options()->SetStringValue("mu_strategy", "adaptive");
	app->Options()->SetStringValue("output_file", "ipopt.out");
	app->Options()->SetIntegerValue("print_level", 0);	//minimum print out in DOS window
	ApplicationReturnStatus status;
	//initialization
	status = app->Initialize();
	if (status != Solve_Succeeded)
	{
		printf("Error during initialization!\n");
		return;
	}
	//solve the problem
	status = app->OptimizeTNLP(mynlp);
	if (status != Solve_Succeeded)
		printf("not solved");
}

void CDabnet::TrainReducedModelNeuralNetwork()
{
	if (ilinear_ann)	//default type is 2
		ann_red.SetHiddenLayerActivationType(0);
	if (pdabnet_input->itrain_red_opt)
		TrainReducedModelNeuralNetworkByIpopt();
	else
		TrainReducedModelNeuralNetworkByBackPropagation();
}

void CDabnet::PrepareLaguerreNeuralNetworkWeightMatrices()
{
	int i, j;
	int istate = 0;
	int nneuron = ann_lag.GetNeuronCountOfFirstHiddenLayerExcludingBias();
	double* pweight = ann_lag.GetWeightPointer();	//1-D array from ANN
	double* psigma = ann_lag.GetSigmaPointer();
	double** ppweight = new double* [nneuron];
	for (i=0; i<ninput; i++)
	{
		for (j=0; j<nneuron; j++)
			ppweight[j] = pweight + j*(nstate_lag+1) + istate;
		lss_list[i].PrepareWeightMatrix(nneuron, ppweight, psigma+istate, pdabnet_input->iscale_lag_opt);
		istate += lss_list[i].nstate;
	}
	delete [] ppweight;
}

void CDabnet::ReduceLaguerreStateSpace()
{
	int i;
	//reduce Laguerre model and update nstate_red
	nstate_red = 0;
	for (i=0; i<ninput; i++)
	{
		rss_list[i].DeleteMemory();		//delete in case already allocated, e.g. read from case file
		lss_list[i].RealizeBalancedStateSpace(&rss_list[i]);
		nstate_red += rss_list[i].nstate;
	}
}

void CDabnet::PredictByLaguerreModel(int np, double** ppin, double** ppout)
{
	//np: the number of the data points
	//ppin: the 2-D array of input data, ppdata in vd_data can be used as ppin for prediction (ignore the output part)
	//ppout: the 2-D array of predicted output values without unscaling, only element at index of ioutput is modified and returned
	int i, j, k, n;
	int nstate_j;
	double* prow;
	double* pann_input = new double [nstate_lag];	//state variables
	double* pann_output = new double [noutput];		//noutput is always 1
	prow = ppin[0];
	for (j=0; j<ninput; j++)
		lss_list[j].InitStateVectorToSteadyState(prow[j]);
	for (i=0; i<np; i++)
	{
		prow = ppin[i];
		n = 0;
		for (j=0; j<ninput; j++)
		{
			//lss_list[j].CalcNextStateVector(prow[j]);
			nstate_j = lss_list[i].nstate;
			for (k=0; k<nstate_j; k++)
				pann_input[n++] = lss_list[j].px[k];
			lss_list[j].CalcNextStateVector(prow[j]);
		}
		if (pdabnet_input->iscale_lag_opt)
			ann_lag.ScaleInputData(pann_input);
		ann_lag.Predict(pann_input,pann_output);
		//since scaling factor for output inside ANN is 1 with 0 mean, no need to unscale output inside ANN
		//ann_lag.UnscaleOutputData(pann_output);
		ppout[i][ioutput] = pann_output[0];
	}
	delete [] pann_input;
	delete [] pann_output;
}

void CDabnet::PredictByReducedModel(int np, double** ppin, double** ppout)
{
	//np: the number of the data points
	//ppin: the 2-D array of input data, ppdata in vd_data can be used for prediction (ignore the output part)
	//pout: the 2-D array of predicted output values without unscaling, only element at index of ioutput is modified and returned
	int i, j, k, n;
	double* prow;
	double* pann_input = new double [nstate_red];
	double* pann_output = new double [noutput];
	prow = ppin[0];
	for (j=0; j<ninput; j++)
		rss_list[j].InitStateVectorToSteadyState(prow[j]);
	for (i=0; i<np; i++)
	{
		prow = ppin[i];
		n = 0;
		for (j=0; j<ninput; j++)
		{
			//rss_list[j].CalcNextStateVector(prow[j]);
			for (k=0; k<rss_list[j].nstate; k++)
				pann_input[n++] = rss_list[j].px[k];
			rss_list[j].CalcNextStateVector(prow[j]);
		}
		if (pdabnet_input->iscale_red_opt)
			ann_red.ScaleInputData(pann_input);
		ann_red.Predict(pann_input,pann_output);
		//since output scaling factor for the ANN is 1 with mean of 0, no need to unscale inside ANN
		//ann_red.UnscaleOutputData(pann_output);
		ppout[i][ioutput] = pann_output[0];
	}
	delete [] pann_input;
	delete [] pann_output;
}

void CDabnet::CalcMeanAndSigmaOfReducedModelStateVariables(int np, double** ppin, double* pmean, double* psigma)
{
	//np: the number of the data points
	//ppin: the 2-D array of input data, ppdata in vd_data can be used for prediction (ignore the output part)
	//psigma: the 1-D array of standard deviation of state variables
	int i, j, k, n;
	double dx;
	double* prow;
	//calculate mean
	for (n=0; n<nstate_red; n++)
		pmean[n] = 0;
	prow = ppin[0];
	for (j=0; j<ninput; j++)
		rss_list[j].InitStateVectorToSteadyState(prow[j]);
	for (i=0; i<np; i++)
	{
		prow = ppin[i];
		n = 0;
		for (j=0; j<ninput; j++)
		{
			for (k=0; k<rss_list[j].nstate; k++)
				pmean[n++] += rss_list[j].px[k];
			rss_list[j].CalcNextStateVector(prow[j]);
		}
	}
	for (n=0; n<nstate_red; n++)
		pmean[n] /= np;
	//calculate sigma
	for (n=0; n<nstate_red; n++)
		psigma[n] = 0;
	prow = ppin[0];
	for (j=0; j<ninput; j++)
		rss_list[j].InitStateVectorToSteadyState(prow[j]);
	for (i=0; i<np; i++)
	{
		prow = ppin[i];
		n = 0;
		for (j=0; j<ninput; j++)
		{
			for (k=0; k<rss_list[j].nstate; k++)
			{
				dx = rss_list[j].px[k] - pmean[n];
				psigma[n++] += dx*dx;
			}
			rss_list[j].CalcNextStateVector(prow[j]);
		}
	}
	if (np<=1)
		np = 2;
	for (n=0; n<nstate_red; n++)
		psigma[n] = sqrt(psigma[n]/(np-1));
}

void CDabnet::PredictByDRM(int np, double** ppin, double** ppout)
{
	if (pdabnet_input->ipredict_opt)	//balanced/reduced model
		PredictByReducedModel(np,ppin,ppout);
	else		//Laguerre model
		PredictByLaguerreModel(np,ppin,ppout);
}

void CDabnet::WriteReducedModelStateSpaceMatrices(FILE* pf)
{
	int i;
	for (i=0; i<ninput; i++)
		rss_list[i].WriteStateSpaceMatrices(pf);
}

void CDabnet::ReadReducedModelStateSpaceMatrices(FILE* pf)
{
	int i;
	nstate_red = 0;
	for (i=0; i<ninput; i++)
	{
		rss_list[i].ReadStateSpaceMatrices(pf);
		nstate_red += rss_list[i].nstate;
	}
}

void CDabnet::WriteLaguerreModelStateSpaceMatrices(FILE* pf)
{
	int i;
	for (i=0; i<ninput; i++)
		lss_list[i].WriteStateSpaceMatrices(pf);
}

void CDabnet::WriteDRMTextFile(FILE* pf)
{
	//write reduced model
	fprintf(pf,"%d\t//number of input variables\n",ninput);
	fprintf(pf,"%d\t//number of output variables\n",noutput);
	fprintf(pf,"//list of matrices\n");
	WriteReducedModelStateSpaceMatrices(pf);
	fprintf(pf,"//neural network data\n");
	ann_red.WriteANNData(pf);
}

void CDabnet::WriteDRMMatlabFile(FILE* pf)
{
	//based on ipredict_opt model option, 0=Laguerre, 1=reduced/balanced
	//does not write the mean and sigma data
	int i, j, k;
	int nstate;
	int ioutput1 = ioutput + 1;		//convert from 0-based index to 1-based index for MATLAB
	double** ppa;
	double* pb;
	if (pdabnet_input->ipredict_opt)		//reduced form
	{
		//for each input, write A B matrices
		for (i=0; i<ninput; i++)
		{
			nstate = rss_list[i].nstate;
			ppa = rss_list[i].ppa;
			fprintf(pf,"A{%d,%d} = [",ioutput1,i+1);
			for (j=0; j<nstate; j++)
			{
				for (k=0; k<nstate; k++)
					fprintf(pf,"%lg ",ppa[j][k]);
				fprintf(pf,"\n");
			}
			fprintf(pf,"];\n");
			pb = rss_list[i].pb;
			fprintf(pf,"B{%d,%d} = [",ioutput1,i+1);
			for (j=0; j<nstate; j++)
				fprintf(pf,"%lg ",pb[j]);
			fprintf(pf,"]\';\n");
		}
		ann_red.WriteANNMatlabFile(pf,ioutput);
	}
	else		//Laguerre form
	{
		//for each input, write A B matrices
		for (i=0; i<ninput; i++)
		{
			nstate = lss_list[i].nstate;
			ppa = lss_list[i].ppa;
			fprintf(pf,"A{%d,%d} = [",ioutput1,i+1);
			for (j=0; j<nstate; j++)
			{
				for (k=0; k<nstate; k++)
					fprintf(pf,"%lg ",ppa[j][k]);
				fprintf(pf,"\n");
			}
			fprintf(pf,"];\n");
			pb = lss_list[i].pb;
			fprintf(pf,"B{%d,%d} = [",ioutput1,i+1);
			for (j=0; j<nstate; j++)
				fprintf(pf,"%lg ",pb[j]);
			fprintf(pf,"]\';\n");
		}
		ann_lag.WriteANNMatlabFile(pf,ioutput);
	}
}

void CDabnet::WriteWeightMatrixFile(FILE* pf)
{
	int i;
	for (i=0; i<ninput; i++)
	{
		fprintf(pf, "Weight matrices for Input %d\n",i+1);
		lss_list[i].mweight.WriteText(pf);
	}
}

PyObject* CDabnet::GetDabnetAsTuple()
{
	int i;
	PyObject* obj_dabnet = PyTuple_New(7);
	PyObject* obj_state_lag;			//list of Laguerre state space
	PyObject* obj_state_red;			//list of reduced state space
	PyObject* obj_ann_lag;				//ANN of Laguerre model
	PyObject* obj_ann_red;				//ANN of reduced model
	PyObject* obj_state;				//a state space tuple object
	PyTuple_SetItem(obj_dabnet, 0, Py_BuildValue("i", ninput));
	PyTuple_SetItem(obj_dabnet, 1, Py_BuildValue("i", noutput));
	PyTuple_SetItem(obj_dabnet, 2, Py_BuildValue("i", ioutput));
	//state space
	obj_state_lag = PyTuple_New(ninput);
	obj_state_red = PyTuple_New(ninput);
	for (i=0; i<ninput; i++)
	{
		obj_state = lss_list[i].GetStateSpaceAsTuple();
		PyTuple_SetItem(obj_state_lag, i, Py_BuildValue("O", obj_state));
	}
	for (i=0; i<ninput; i++)
	{
		obj_state = rss_list[i].GetStateSpaceAsTuple();
		PyTuple_SetItem(obj_state_red, i, Py_BuildValue("O", obj_state));
	}
	//ANN
	obj_ann_lag = ann_lag.GetAnnAsTuple();
	obj_ann_red = ann_red.GetAnnAsTuple();
	//assign to obj_dabnet
	PyTuple_SetItem(obj_dabnet, 3, Py_BuildValue("O", obj_state_lag));
	PyTuple_SetItem(obj_dabnet, 4, Py_BuildValue("O", obj_ann_lag));
	PyTuple_SetItem(obj_dabnet, 5, Py_BuildValue("O", obj_state_red));
	PyTuple_SetItem(obj_dabnet, 6, Py_BuildValue("O", obj_ann_red));
	return obj_dabnet;
}