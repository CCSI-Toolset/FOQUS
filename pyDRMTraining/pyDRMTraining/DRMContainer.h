//DRMContainer.h
#ifndef __DRMCONTAINER_H__
#define __DRMCONTAINER_H__

#include <vector>
#include "DataCollection.h"
#include "Narma.h"
#include "Dabnet.h"
#include "Python.h"

//steps to generate a DRM
//1. assign data_varied
//2. set imodel_type
//3. set ninput and noutput
//4. call InitDabnet() or InitNarma()
//4. set dabnet_input if DABNet, nhistory and other options if NARMA
//5. set Laguerre order list and pole list for each output/input pair, number of neurons if DABNet
//6. call GenerateDRM()
class CDRMContainer
{
public:
	int imodel_type;								//model type, 0=DABNet, 1=NARMA
	int ninput;										//number of input variables (size of vector)
	int noutput;									//number of output variables
	std::vector<double> mean_state_red;				//mean of reduced model state variables
	std::vector<double> sigma_state_red;			//standard deviation of reduced model state variables
	CDataCollection data_varied;					//data containing the varied input and output variables (excluding constant input variables), vector size: ninput + noutput
	CNarma drm_narma;								//D-RM based on NARMA model
	CDabnetInput dabnet_input;						//DABNet model parameters and options
	std::vector<CDabnet> drm_dabnet;				//D-RM based on DABNet model, one for each output variable

	CDRMContainer(void);
	virtual ~CDRMContainer(void);
	void SetModelType(int i) {imodel_type = i;}
	void SetNumberOfInputs(int n) {ninput = n;}
	void SetNumberOfOutputs(int n) {noutput = n;}
	void InitDabnet();
	void InitNarma();
	void WriteWeightMatrixFile(FILE* pf);
	void WriteDRMTextFile(FILE* pf);
	void WriteDRMMatlabFile(FILE* pf);
	void GenerateDRM();
	void CalcMeanAndSigmaOfReducedModelStateVariables();
	PyObject* GetDRMAsTuple();
};

#endif