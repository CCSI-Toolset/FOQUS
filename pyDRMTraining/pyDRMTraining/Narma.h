//Narma.h
#ifndef __NARMA_H__
#define __NARMA_H__

#include <vector>
#include "DataCollection.h"
#include "NeuralNetwork.h"
#include "Python.h"

class CNarma
{
public:
	int ipredict_opt;								//prediction option 0=use high-fidelity model output for history data 1=use D-RM output for history data
	int ninput;										//number of input variables (size of vector)
	int noutput;									//number of output variables
	int nhistory;									//number of history points used for NARMA model
	int nneuron_hid;								//number of neurons in hidden layer
	int nmax_iter_bp;								//maximum iteration number for NARMA model BP training
	CDataCollection ann_data;						//data for ANN (training or validation)
	CNeuralNetwork ann;								//NARMA model artificial network

	//pointers related to meta data set in CDRMContainer
	CDataCollection* pid_data;						//plant identification data

	CNarma(void);
	virtual ~CNarma(void);
	void SetNumberOfInputs(int n) {ninput = n;}
	void SetNumberOfOutputs(int n) {noutput = n;}
	void ProcessIdentificationDataForTraining();
	void TrainNeuralNetwork();
	void PredictByDRM(int np, double** ppin, double**ppout);
	void WriteDRMTextFile(FILE* pf);
	void WriteDRMMatlabFile(FILE* pf);
	PyObject* GetNarmaAsTuple();
};

#endif