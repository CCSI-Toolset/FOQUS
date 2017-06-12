//DRMContainer.cpp
#include <math.h>
#include "Simplex.h"
#include "DRMContainer.h"

CDRMContainer::CDRMContainer(void)
{
	imodel_type = 0;
	ninput = 1;
	noutput = 0;
}

CDRMContainer::~CDRMContainer(void)
{
}

void CDRMContainer::InitDabnet()
{
	//assume ninput, noutput has been set
	int i;
	drm_dabnet.clear();
	drm_dabnet.resize(noutput);
	//set default pole, order data
	//the actual data will be provided by GUI with total number of Laguerre states updated inside the GUI
	for (i=0; i<noutput; i++)
	{
		drm_dabnet[i].ninput = ninput;
		drm_dabnet[i].noutput = 1;
		drm_dabnet[i].ioutput = i;
		drm_dabnet[i].ResizeVectors(ninput);
		drm_dabnet[i].pid_data = &data_varied;
		drm_dabnet[i].pdabnet_input = &dabnet_input;
	}
}

void CDRMContainer::InitNarma()
{
	//assume ninput, noutput has been set
	drm_narma.ninput = ninput;
	drm_narma.noutput = noutput;
	drm_narma.pid_data = &data_varied;
}

void CDRMContainer::WriteWeightMatrixFile(FILE* pf)
{
	int i;
	for (i=0; i<noutput; i++)
	{
		fprintf(pf,"Weight matrices for Output %d\n",i+1);
		drm_dabnet[i].WriteWeightMatrixFile(pf);
	}
}

void CDRMContainer::WriteDRMTextFile(FILE* pf)
{
	int i;
	fprintf(pf,"%d\t//number of input variables\n",ninput);
	fprintf(pf,"%d\t//number of output variables\n",noutput);
	fprintf(pf,"//mean of training input data\n");
	for (i=0; i<ninput; i++)
		fprintf(pf,"%lg\t", data_varied.pmean[i]);
	fprintf(pf,"\n");
	fprintf(pf,"//standard deviation of training input data\n");
	for (i=0; i<ninput; i++)
		fprintf(pf,"%lg\t", data_varied.psigma[i]);
	fprintf(pf,"\n");
	fprintf(pf,"//mean of training output data\n");
	for (i=0; i<noutput; i++)
		fprintf(pf,"%lg\t", data_varied.pmean[i+ninput]);
	fprintf(pf,"\n");
	fprintf(pf,"//standard deviation of training output data\n");
	for (i=0; i<noutput; i++)
		fprintf(pf,"%lg\t", data_varied.psigma[i+ninput]);
	fprintf(pf,"\n");
	//write model data
	if (imodel_type==0)	//DABNet model
	{
		//always write the reduced form
		for (i=0; i<noutput; i++)
			drm_dabnet[i].WriteDRMTextFile(pf);
	}
	else	//NARMA model
		drm_narma.WriteDRMTextFile(pf);
	
}

void CDRMContainer::WriteDRMMatlabFile(FILE* pf)
{
	int i;
	//numbers of inputs and outputs
	fprintf(pf,"nu = %d;\n",ninput);
	fprintf(pf,"ny = %d;\n",noutput);
	//write mean and sigma of input and output data
	for (i=0; i<ninput; i++)
		fprintf(pf,"u_mean(%d) = %lg;\n",i+1,data_varied.pmean[i]);
	for (i=0; i<noutput; i++)
		fprintf(pf,"y_mean(%d) = %lg;\n",i+1,data_varied.pmean[i+ninput]);
	for (i=0; i<ninput; i++)
		fprintf(pf,"u_sigma(%d) = %lg;\n",i+1,data_varied.psigma[i]);
	for (i=0; i<noutput; i++)
		fprintf(pf,"y_sigma(%d) = %lg;\n",i+1,data_varied.psigma[i+ninput]);
	if (imodel_type==0)	//DABNet model
	{
		for (i=0; i<noutput; i++)
			drm_dabnet[i].WriteDRMMatlabFile(pf);
	}
	else	//NARMA model
		drm_narma.WriteDRMMatlabFile(pf);
}

void CDRMContainer::GenerateDRM()
{
	//generate either DABNet or NARMA model
	int i, j, k;
	int npole;			//number of poles that needs to be optimized (each input may contain up to 2 poles)
	printf("Starting to generate D-RM. It takes a while to train neural network. Please wait...\n");
	//no need to read data but need to filter out the constant variables
	data_varied.CalcMeanAndSigma();
	data_varied.ScaleInputData();
	data_varied.ScaleOutputData();
	//start to build DRM
	if (imodel_type==0)	//DABNet model
	{
		for (j=0; j<noutput; j++)
		{
			printf("Building DABNet model for output %d...\n",j+1);
			drm_dabnet[j].lss_list.clear();
			drm_dabnet[j].rss_list.clear();
			drm_dabnet[j].CreateLaguerreStateSpaceList();
			drm_dabnet[j].UpdateTotalLaguerreOrders();
			drm_dabnet[j].ResizeReducedModelStateSpaceList();
			//calculate number of poles that need to be optimized
			switch (drm_dabnet[j].ipole_opt)
			{
			case 0:
				npole = 0;
				break;
			case 1:
				npole = ninput;
				for (i=0; i<ninput; i++)
				{
					if (drm_dabnet[j].ipole2_list[i])
						npole++;
				}
				break;
			case 2:
				npole = ninput;
				break;
			case 3:
				npole = 0;
				for (i=0; i<ninput; i++)
				{
					if (drm_dabnet[j].ipole2_list[i])
						npole++;
				}
				break;
			default:
				npole = 0;
			}
			if (npole)	//optimize the pole values using user specified as initial guess
			{
				printf("Optimize Laguerre poles...\n");
				CSimplex sp;
				CObjectiveFunction objfunc;
				objfunc.SetModel(&drm_dabnet[j]);
				objfunc.ResetCounter();
				double* ppole = new double [npole];		//initial pole values
				double* plen = new double [npole];
				double* pmax = new double [npole];
				double* pmin = new double [npole];
				sp.SetNvar(npole);
				sp.SetObjectiveFunctionPointer(&objfunc);
				sp.AllocateMemory();
				k = 0;
				if (drm_dabnet[j].ipole_opt==1 || drm_dabnet[j].ipole_opt==2)
				{
					for (i=0; i<ninput; i++)
						ppole[k++] = drm_dabnet[j].pole_list[i];
				}
				if (drm_dabnet[j].ipole_opt==1 || drm_dabnet[j].ipole_opt==3)
				{
					for (i=0; i<ninput; i++)
					{
						if (drm_dabnet[j].ipole2_list[i])
							ppole[k++] = drm_dabnet[j].pole2_list[i];
					}
				}
				for (i=0; i<npole; i++)
				{
					plen[i] = 0.1;
					pmax[i] = 0.9999;
					pmin[i] = 0.001;
				}
				sp.InitSimplex(ppole,plen,pmax,pmin);
				sp.Optimize();
				delete [] ppole;
				delete [] plen;
				delete [] pmax;
				delete [] pmin;
				//pole_list now has the optimized values
				printf("Optimized Laguerre pole values are listed below.\n");
				if (drm_dabnet[j].ipole_opt==1 || drm_dabnet[j].ipole_opt==2)
				{
					for (i=0; i<ninput; i++)
						printf("Input %d Fast Pole: %lg\n", i+1, drm_dabnet[j].pole_list[i]);
				}
				if (drm_dabnet[j].ipole_opt==1 || drm_dabnet[j].ipole_opt==3)
				{
					for (i=0; i<ninput; i++)
					{
						if (drm_dabnet[j].ipole2_list[i])
							printf("Input %d Slow Pole: %lg\n", i+1, drm_dabnet[j].pole2_list[i]);
					}
				}
			}
			else	//use user specified pole values
			{
				//train Laguerre model
				printf("Training Laguerre model neural network...\n");
				drm_dabnet[j].ProcessIdentificationDataForLaguerreTraining();
				drm_dabnet[j].TrainLaguerreNeuralNetwork();
			}
			//train reduced model
			printf("Reducing order of state space through balanced realization...\n");
			drm_dabnet[j].PrepareLaguerreNeuralNetworkWeightMatrices();
			printf("Done with weight matrix\n");
			drm_dabnet[j].ReduceLaguerreStateSpace();
			//prepare message
			printf("Numbers of state-space variables are [");
			for (i=0; i<ninput; i++)
			{
				printf("%d",drm_dabnet[j].rss_list[i].nstate);
				if (i<ninput-1)
					printf(" ");
				else
					printf("].\n");
			}
			drm_dabnet[j].ProcessIdentificationDataForReducedModelTraining();
			printf("Training balanced model neural network...\n");
			drm_dabnet[j].TrainReducedModelNeuralNetwork();
		}
		printf("D-RM has been generated.\n");
	}
	else		//NARMA model
	{
		printf("Training neural network...\n");
		drm_narma.ProcessIdentificationDataForTraining();
		drm_narma.TrainNeuralNetwork();
		printf("D-RM has been generated.\n");
	}
}

void CDRMContainer::CalcMeanAndSigmaOfReducedModelStateVariables()
{
	if (imodel_type)	//NARMA model, do nothing
		return;
	int i, j;
	int nstate_total = 0;
	for (i=0; i<noutput; i++)
		nstate_total += drm_dabnet[i].nstate_red;
	mean_state_red.resize(nstate_total);
	sigma_state_red.resize(nstate_total);
	j = 0;
	for (i=0; i<noutput; i++)
	{
		drm_dabnet[i].CalcMeanAndSigmaOfReducedModelStateVariables(data_varied.npair, data_varied.ppdata, &mean_state_red[j], &sigma_state_red[j]);
		j += drm_dabnet[i].nstate_red;
	}
}

PyObject* CDRMContainer::GetDRMAsTuple()
{
	int i, j;
	int nstate_all;
	PyObject* obj_result = PyTuple_New(2);		//tuple to be returned
	PyObject* obj_drm;							//tuple of DRM
	PyObject* obj_mean_input;
	PyObject* obj_sigma_input;
	PyObject* obj_mean_output;
	PyObject* obj_sigma_output;
	PyObject* obj_mean_state;
	PyObject* obj_sigma_state;
	PyObject* obj_narma;
	PyObject* obj_dabnet;
	PyObject* obj_dabnet_list;
	PyObject* obj_pole_list;
	PyTuple_SetItem(obj_result, 0, Py_BuildValue("i", imodel_type));
	if (imodel_type)	//NARMA model
		obj_drm = PyTuple_New(7);
	else
		obj_drm = PyTuple_New(10);		//added pole list
	PyTuple_SetItem(obj_drm, 0, Py_BuildValue("i", ninput));
	PyTuple_SetItem(obj_drm, 1, Py_BuildValue("i", noutput));
	//mean and sigma of input
	obj_mean_input = PyTuple_New(ninput);
	obj_sigma_input = PyTuple_New(ninput);
	for (i=0; i<ninput; i++)
	{
		PyTuple_SetItem(obj_mean_input, i, Py_BuildValue("d", data_varied.pmean[i]));
		PyTuple_SetItem(obj_sigma_input, i, Py_BuildValue("d", data_varied.psigma[i]));
	}
	PyTuple_SetItem(obj_drm, 2, Py_BuildValue("O", obj_mean_input));
	PyTuple_SetItem(obj_drm, 3, Py_BuildValue("O", obj_sigma_input));
	//mean and sigma of output
	obj_mean_output = PyTuple_New(noutput);
	obj_sigma_output = PyTuple_New(noutput);
	for (i=0; i<noutput; i++)
	{
		PyTuple_SetItem(obj_mean_output, i, Py_BuildValue("d", data_varied.pmean[i+ninput]));
		PyTuple_SetItem(obj_sigma_output, i, Py_BuildValue("d", data_varied.psigma[i+ninput]));
	}
	PyTuple_SetItem(obj_drm, 4, Py_BuildValue("O", obj_mean_output));
	PyTuple_SetItem(obj_drm, 5, Py_BuildValue("O", obj_sigma_output));
	if (imodel_type)	//NARMA model
	{
		obj_narma = drm_narma.GetNarmaAsTuple();
		PyTuple_SetItem(obj_drm, 6, Py_BuildValue("O", obj_narma));
	}
	else
	{
		obj_dabnet_list = PyTuple_New(noutput);
		for (i=0; i<noutput; i++)
		{
			obj_dabnet = drm_dabnet[i].GetDabnetAsTuple();
			PyTuple_SetItem(obj_dabnet_list, i, Py_BuildValue("O", obj_dabnet));
		}
		PyTuple_SetItem(obj_drm, 6, Py_BuildValue("O", obj_dabnet_list));
		//mean and sigma of state variables
		nstate_all = mean_state_red.size();
		obj_mean_state = PyTuple_New(nstate_all);
		obj_sigma_state = PyTuple_New(nstate_all);
		for (i=0; i<nstate_all; i++)
		{
			PyTuple_SetItem(obj_mean_state, i, Py_BuildValue("d", mean_state_red[i]));
			PyTuple_SetItem(obj_sigma_state, i, Py_BuildValue("d", sigma_state_red[i]));
		}
		PyTuple_SetItem(obj_drm, 7, Py_BuildValue("O", obj_mean_state));
		PyTuple_SetItem(obj_drm, 8, Py_BuildValue("O", obj_sigma_state));
		//add optimized pole values
		obj_pole_list = PyTuple_New(noutput*ninput*2);
		for (i=0; i<noutput; i++)
		{
			for (j=0; j<ninput; j++)
			{
				PyTuple_SetItem(obj_pole_list, (i*ninput+j)*2, Py_BuildValue("d", drm_dabnet[i].pole_list[j]));
				PyTuple_SetItem(obj_pole_list, (i*ninput+j)*2+1, Py_BuildValue("d", drm_dabnet[i].pole2_list[j]));
			}
		}
		PyTuple_SetItem(obj_drm, 9, Py_BuildValue("O", obj_pole_list));
	}
	//finally add the second tuple element of DRM object
	PyTuple_SetItem(obj_result, 1, Py_BuildValue("O", obj_drm));
	return obj_result;
}